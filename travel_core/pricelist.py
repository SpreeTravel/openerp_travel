# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010, 2014 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


from openerp import api, tools
from openerp.exceptions import except_orm
from openerp import fields
from openerp.models import Model, TransientModel
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
import ho.pisa as pisa
import time
import xlwt
import base64
import cStringIO

FIELD_TYPES = {'date': 1, 'many2one': 5, 'float': 3, 'integer': 4}
CORE_FIELDS = [
    (1, 'start_date', 'Start Date'),
    (1, 'end_date', 'End Date'),
    (2, 'price', 'Price'),
    (3, 'child', 'Child')
]


def fix(chain):
    chain = chain.split('_')
    if len(chain) > 2:
        res = ''
        for x in range(0, len(chain) - 2):
            res += chain[x] + ' '
        res += chain[len(chain) - 2]
        return res
    else:
        return chain[0]


def remove_wrong_characters(string):
    for x in ['/', '\\', '?', '*', '-', '[', ']']:
        string = string.replace(x, ' ')

    if len(string) > 32:
        return string[:30]
    else:
        return string


class product_pricelist(Model):
    _name = 'product.pricelist'
    _inherit = 'product.pricelist'

    @api.one
    def _get_items(self):
        result = False
        for v in self.version_id:
            result += v.items_id
        self.pricelist_item_ids = result

    @api.model
    def _get_version_id(self):
        version_obj = self.env['product.pricelist.version']

        if self.version_id:
            version_id = self.version_id[0].id
        else:
            version_vals = {
                'name': 'Default Version',
                'pricelist_id': self.id,
                'active': True
            }
            version_id = version_obj.create(version_vals)
        return version_id

    @api.one
    def _set_items(self):
        ppi_obj = self.env['product.pricelist.item']
        for v in self.pricelist_item_ids:
            if v[0] == 0:
                version_id = self._get_version_id()
                v[2].update({'price_version_id': version_id})
                ppi_obj.create(v[2])
            elif v[0] == 1:
                ppi_obj.write(v[1], v[2])
            elif v[0] == 2:
                ppi_obj.unlink(v[1])
        return True

    pricelist_item_ids = fields.One2many(compute=_get_items, method=True,
                                         inverse=_set_items,
                                         string='Items',
                                         relation='product.pricelist.item')

    @api.multi
    def set_conditions(self):
        import datetime
        if len(self):
            element = self[0]

            pool = self.env['customer.price']
            obj = pool.create({
                'pricelist': element.id,
                'start_date': datetime.datetime.now(),
                'end_date': datetime.datetime.now()
            })
            return {
                "name": 'Export Prices',
                "type": 'ir.actions.act_window',
                "res_model": 'customer.price',
                "view_type": 'form',
                "view_mode": 'form',
                "target": 'new',
                'res_id': obj.id
            }

    def _calculate_price_by_supplier(self, cr, uid, seller, qty, product, product_uom_obj, context):
        price = None
        uom_price_already_computed = False
        qty_in_seller_uom = qty
        from_uom = context.get('uom') or product.uom_id.id
        seller_uom = seller.product_uom and seller.product_uom.id or False
        if seller_uom and from_uom and from_uom != seller_uom:
            qty_in_seller_uom = product_uom_obj._compute_qty(cr, uid, from_uom, qty, to_uom_id=seller_uom)
        else:
            uom_price_already_computed = True
        params = context.get('params', {})
        for line in seller.pricelist_ids:
            if line.min_quantity <= qty_in_seller_uom:
                # price = line.price
                price = product.price_get_partner(product.id, seller.id, params)
        return price, uom_price_already_computed

    def _price_rule_get_multi(self, cr, uid, pricelist, products_by_qty_by_partner, context=None):
        context = context or {}
        date = context.get('date') or time.strftime('%Y-%m-%d')

        products = map(lambda x: x[0], products_by_qty_by_partner)
        currency_obj = self.pool.get('res.currency')
        product_obj = self.pool.get('product.template')
        product_uom_obj = self.pool.get('product.uom')
        price_type_obj = self.pool.get('product.price.type')

        if not products:
            return {}

        version = False
        for v in pricelist.version_id:
            if ((v.date_start is False) or (v.date_start <= date)) and ((v.date_end is False) or (v.date_end >= date)):
                version = v
                break
        if not version:
            raise except_orm(_('Warning!'),
                             _("At least one pricelist has no active version !\nPlease create or activate one."))
        categ_ids = {}
        for p in products:
            categ = p.categ_id
            while categ:
                categ_ids[categ.id] = True
                categ = categ.parent_id
        categ_ids = categ_ids.keys()

        is_product_template = products[0]._name == "product.template"
        if is_product_template:
            prod_tmpl_ids = [tmpl.id for tmpl in products]
            prod_ids = [product.id for product in tmpl.product_variant_ids for tmpl in products]
        else:
            prod_ids = [product.id for product in products]
            prod_tmpl_ids = [product.product_tmpl_id.id for product in products]

        # Load all rules
        cr.execute(
            'SELECT i.id '
            'FROM product_pricelist_item AS i '
            'WHERE (product_tmpl_id IS NULL OR product_tmpl_id = any(%s)) '
            'AND (product_id IS NULL OR (product_id = any(%s))) '
            'AND ((categ_id IS NULL) OR (categ_id = any(%s))) '
            'AND (price_version_id = %s) '
            'ORDER BY sequence, min_quantity desc',
            (prod_tmpl_ids, prod_ids, categ_ids, version.id))

        item_ids = [x[0] for x in cr.fetchall()]
        items = self.pool.get('product.pricelist.item').browse(cr, uid, item_ids, context=context)

        price_types = {}

        results = {}
        for product, qty, partner in products_by_qty_by_partner:
            if hasattr(product, 'product_tmpl_id'):
                pass
            else:
                prod_prod = self.pool.get('product.product')
                product_ids = prod_prod.search(cr, uid, [('product_tmpl_id', '=', product.id)])
                product = prod_prod.browse(cr, uid, product_ids)
            uom_price_already_computed = False
            results[product.id] = 0.0
            price = False
            rule_id = False
            for rule in items:
                if rule.min_quantity and qty < rule.min_quantity:
                    continue
                if is_product_template:
                    if rule.product_tmpl_id and product.id != rule.product_tmpl_id.id:
                        continue
                    if rule.product_id:
                        continue
                else:
                    if rule.product_tmpl_id and product.product_tmpl_id.id != rule.product_tmpl_id.id:
                        continue
                    if rule.product_id and product.id != rule.product_id.id:
                        continue

                if rule.categ_id:
                    cat = product.categ_id
                    while cat:
                        if cat.id == rule.categ_id.id:
                            break
                        cat = cat.parent_id
                    if not cat:
                        continue

                if rule.base == -1:
                    if rule.base_pricelist_id:
                        price_tmp = self._price_get_multi(cr, uid,
                                                          rule.base_pricelist_id, [(product,
                                                                                    qty, False)], context=context)[
                            product.id]
                        ptype_src = rule.base_pricelist_id.currency_id.id
                        uom_price_already_computed = True
                        price = currency_obj.compute(cr, uid,
                                                     ptype_src, pricelist.currency_id.id,
                                                     price_tmp, round=False,
                                                     context=context)
                elif rule.base == -2:
                    sup_id = context.get('supplier_id', False)
                    supplierinfo_obj = self.pool.get('product.supplierinfo')
                    where = []
                    if partner:
                        where = [('name', '=', sup_id)]
                    sinfo = supplierinfo_obj.search(cr, uid,
                                                    [('product_tmpl_id', '=', product.product_tmpl_id.id)] + where)
                    price = 0.0
                    product_package = self.pool.get('product.package')
                    pp_id = product_package.search(cr, uid, [('product_id', '=', product.id)])
                    product_package_elmt = None
                    if len(pp_id):
                        product_package_elmt = product_package.browse(cr, uid, pp_id)

                    if len(sinfo) > 0 and len(product.seller_ids):
                        for seller in product.seller_ids:
                            # I dont get this condition, what they meant
                            # if (not partner) or (seller.name.id != partner):
                            #    continue
                            if seller.id == sinfo[0]:
                                price, uom_price_already_computed = self._calculate_price_by_supplier(cr, uid,
                                                                                                      seller,
                                                                                                      qty,
                                                                                                      product,
                                                                                                      product_uom_obj,
                                                                                                      context)
                    elif product_package_elmt:
                        try:
                            package_lines = context['params']['package_lines']
                        except KeyError:
                            package_lines = None
                        if package_lines:
                            res = []
                            solpl = self.pool.get('sale.order.line.package.line')
                            for x in package_lines:
                                _id = x[1]
                                if _id:
                                    ids = solpl.search(cr, uid, [('id', '=', _id)])
                                    solpl_elemnt = solpl.browse(cr, uid, ids)
                                    res.append((solpl_elemnt.order, solpl_elemnt.supplier_id.id))
                                else:
                                    try:
                                        res.append((x[2]['order'], x[2]['supplier_id']))
                                    except KeyError:
                                        continue
                            for sol_line in res:
                                if sol_line:
                                    for x in product_package_elmt.product_line_ids:
                                        if x.order == sol_line[0]:
                                            line = x
                                    res_partner = self.pool.get('product.supplierinfo')
                                    ids = res_partner.search(cr, uid, [('name', '=', sol_line[1]), (
                                        'product_tmpl_id', '=', line.product_id.product_tmpl_id.id)])
                                    supplier_id = res_partner.browse(cr, uid, ids)
                                    tmp, uom_price_already_computed = self._calculate_price_by_supplier(cr, uid,
                                                                                                        supplier_id,
                                                                                                        qty,
                                                                                                        line.product_id,
                                                                                                        product_uom_obj,
                                                                                                        context)
                                    if tmp:
                                        price += tmp
                                    else:
                                        price = product.list_price
                                        break
                                else:
                                    price = product.list_price
                                    break
                    else:
                        price = product.list_price

                else:
                    if rule.base not in price_types:
                        price_types[rule.base] = price_type_obj.browse(cr, uid, int(rule.base))
                    price_type = price_types[rule.base]

                    uom_price_already_computed = True
                    price = currency_obj.compute(cr, uid,
                                                 price_type.currency_id.id, pricelist.currency_id.id,
                                                 product_obj._price_get(cr, uid, [product],
                                                                        price_type.field, context=context)[product.id],
                                                 round=False, context=context)

                if price:
                    params = context.get('params', {})
                    paxs = self.pool.get('sale.order.line').get_total_paxs(cr, uid, params, context)
                    days = self.pool.get('sale.order.line').get_margin_days(cr, uid, params, context)
                    price_limit = price
                    price += days * paxs * (rule.margin_per_pax or 0.0)
                    price *= 1.0 + (rule.price_discount or 0.0)
                    if rule.price_round:
                        price = tools.float_round(price, precision_rounding=rule.price_round)
                    price += (rule.price_surcharge or 0.0)
                    if rule.price_min_margin:
                        price = max(price, price_limit + rule.price_min_margin)
                    if rule.price_max_margin:
                        price = min(price, price_limit + rule.price_max_margin)
                    rule_id = rule.id
                break

            if price:
                if 'uom' in context and not uom_price_already_computed:
                    uom = product.uos_id or product.uom_id
                    price = product_uom_obj._compute_price(cr, uid, uom.id, price, context['uom'])

            results[product.id] = (price, rule_id)
        return results

    def price_get_multi(self, cr, uid, pricelist_ids,
                        products_by_qty_by_partner, context=None):

        def _create_parent_category_list(id, lst):
            if not id:
                return []
            parent = product_category_tree.get(id)
            if parent:
                lst.append(parent)
                return _create_parent_category_list(parent, lst)
            else:
                return lst

        # _create_parent_category_list

        if context is None:
            context = {}

        date = time.strftime('%Y-%m-%d')
        if 'date' in context:
            date = context['date']

        currency_obj = self.pool.get('res.currency')
        product_obj = self.pool.get('product.product')
        product_category_obj = self.pool.get('product.category')
        product_uom_obj = self.pool.get('product.uom')
        price_type_obj = self.pool.get('product.price.type')
        pricelist_obj = self.pool.get('product.pricelist')
        version_obj = self.pool.get('product.pricelist.version')

        # product.pricelist.version:
        if not pricelist_ids:
            pricelist_ids = pricelist_obj.search(cr, uid, [], context=context)

        pricelist_version_ids = version_obj.search(cr, uid, [
            ('pricelist_id', 'in', pricelist_ids),
            '|',
            ('date_start', '=', False),
            ('date_start', '<=', date),
            '|',
            ('date_end', '=', False),
            ('date_end', '>=', date),
        ])
        if len(pricelist_ids) != len(pricelist_version_ids):
            raise except_orm(_('Warning!'),
                             _("At least one pricelist has no active version !\nPlease create or activate one."))

        # product.product:
        product_ids = [i[0] for i in products_by_qty_by_partner]
        # products = dict([(item['id'], item) for item in product_obj.read(cr, uid, product_ids, ['categ_id', 'product_tmpl_id', 'uos_id', 'uom_id'])])
        products = product_obj.browse(cr, uid, product_ids, context=context)
        products_dict = dict([(item.id, item) for item in products])

        # product.category:
        product_category_ids = product_category_obj.search(cr, uid, [])
        product_categories = product_category_obj.read(cr, uid, product_category_ids, ['parent_id'])
        product_category_tree = dict(
            [(item['id'], item['parent_id'][0]) for item in product_categories if item['parent_id']])

        results = {}
        for product_id, qty, partner in products_by_qty_by_partner:
            for pricelist_id in pricelist_ids:
                price = False

                tmpl_id = products_dict[product_id].product_tmpl_id and products_dict[
                    product_id].product_tmpl_id.id or False

                categ_id = products_dict[product_id].categ_id and products_dict[product_id].categ_id.id or False
                categ_ids = _create_parent_category_list(categ_id, [categ_id])
                if categ_ids:
                    categ_where = '(categ_id IN (' + ','.join(map(str, categ_ids)) + '))'
                else:
                    categ_where = '(categ_id IS NULL)'

                supplier_where = ''
                if context.get('supplier_id', False):
                    supplier_id = context['supplier_id']
                    supplier_where = 'supplier_id = ' + str(supplier_id) + ' OR '
                supplier_where += 'supplier_id IS NULL'

                if partner:
                    partner_where = 'base <> -2 OR %s IN (SELECT name FROM product_supplierinfo WHERE product_id = %s) '
                    partner_args = (partner, tmpl_id)
                    if context.get('supplier_id', False):
                        partner_args = (context['supplier_id'], tmpl_id)
                else:
                    partner_where = 'base <> -2 '
                    partner_args = ()

                cr.execute(
                    'SELECT i.*, pl.currency_id '
                    'FROM product_pricelist_item AS i, '
                    'product_pricelist_version AS v, product_pricelist AS pl '
                    'WHERE (product_tmpl_id IS NULL OR product_tmpl_id = %s) '
                    'AND (product_id IS NULL OR product_id = %s) '
                    'AND (' + categ_where + ' OR (categ_id IS NULL)) '
                                            'AND (' + supplier_where + ') '
                                                                       'AND (' + partner_where + ') '
                                                                                                 'AND price_version_id = %s '
                                                                                                 'AND (min_quantity IS NULL OR min_quantity <= %s) '
                                                                                                 'AND i.price_version_id = v.id AND v.pricelist_id = pl.id '
                                                                                                 'ORDER BY sequence',
                    (tmpl_id, product_id) + partner_args + (pricelist_version_ids[0], qty))
                res1 = cr.dictfetchall()
                uom_price_already_computed = False
                for res in res1:
                    if res:
                        if res['base'] == -1:
                            if not res['base_pricelist_id']:
                                price = 0.0
                            else:
                                price_tmp = self.price_get(cr, uid,
                                                           [res['base_pricelist_id']], product_id,
                                                           qty, partner, context=context)[res['base_pricelist_id']]
                                ptype_src = self.browse(cr, uid, res['base_pricelist_id']).currency_id.id
                                uom_price_already_computed = True
                                price = currency_obj.compute(cr, uid, ptype_src, res['currency_id'], price_tmp,
                                                             round=False)
                        elif res['base'] == -2:
                            # TODO: revisar que funcione bien el cambio de moneda
                            sup_id = context.get('supplier_id', False)
                            supplierinfo_obj = self.pool.get('product.supplierinfo')
                            where = []
                            if partner:
                                where = [('name', '=', sup_id)]
                            sinfo = supplierinfo_obj.search(cr, uid,
                                                            [('product_id', '=', tmpl_id)] + where)
                            price = 0.0
                            if sinfo:
                                params = context.get('params', {})
                                price = product_obj.price_get_partner(cr, uid, product_id, sinfo[0], params, context)
                        else:
                            price_type = price_type_obj.browse(cr, uid, int(res['base']))
                            uom_price_already_computed = True
                            price = currency_obj.compute(cr, uid,
                                                         price_type.currency_id.id, res['currency_id'],
                                                         product_obj.price_get(cr, uid, [product_id],
                                                                               price_type.field, context=context)[
                                                             product_id], round=False, context=context)

                        params = context.get('params', {})
                        paxs = self.pool.get('sale.order.line').get_total_paxs(cr, uid, params, context)
                        days = self.pool.get('sale.order.line').get_margin_days(cr, uid, params, context)
                        if price is not False:
                            price_limit = price
                            price += days * paxs * (res['margin_per_pax'] or 0.0)
                            price *= 1.0 + (res['price_discount'] or 0.0)
                            price += (res['price_surcharge'] or 0.0)
                            if res['price_min_margin']:
                                price = max(price, price_limit + res['price_min_margin'])
                            if res['price_max_margin']:
                                price = min(price, price_limit + res['price_max_margin'])
                            break

                    else:
                        # False means no valid line found ! But we may not raise an
                        # exception here because it breaks the search
                        price = False

                if price:
                    results['item_id'] = res['id']
                    if 'uom' in context and not uom_price_already_computed:
                        product = products_dict[product_id]
                        uom = product.uos_id or product.uom_id
                        price = product_uom_obj._compute_price(cr, uid, uom.id, price, context['uom'])

                if results.get(product_id):
                    results[product_id][pricelist_id] = price
                else:
                    results[product_id] = {pricelist_id: price}

        return results


class product_pricelist_item(Model):
    _inherit = 'product.pricelist.item'

    margin_per_pax = fields.Float('Margin per Pax',
                                  digits_compute=dp.get_precision('Product Price'))
    supplier_id = fields.Many2one('res.partner', 'Supplier',
                                  domain=[('supplier', '=', True)])


class customer_price(TransientModel):
    _name = 'customer.price'

    pricelist = fields.Many2one('product.pricelist', _('Pricelist'))
    client = fields.Char(_('Client'))
    start_date = fields.Date(_('Start date'))
    end_date = fields.Date(_('End date'))
    category = fields.Many2one('product.category', _('Category'),
                               domain=[('name', '!=', 'All'), ('name', '!=', 'Saleable'),
                                       ('name', '!=', 'Miscellaneous')])
    supplier = fields.Many2one('res.partner', _('Supplier'))

    excel_file = fields.Binary('Excel File')
    excel_name = fields.Char('Excel Name', readonly=True, default='Price_customers.xls')
    pdf_file = fields.Binary('PDF File')
    pdf_name = fields.Char('PDF Name', readonly=True, default='Price_customers.pdf')

    @api.multi
    def export_prices(self):
        wb = xlwt.Workbook()
        body = """
                <html>
                  <head>
                    <meta name="pdfkit-page-size" content="Legal"/>
                    <meta name="pdfkit-orientation" content="Landscape"/>
                  </head>

                  """
        final = """
                </html>
                """

        obj = self[0]

        if obj.category and obj.supplier:
            category_name = obj.category.name.lower()
            product_category = self.env['product.' + category_name]
            supplier_info = self.env['product.supplierinfo']
            supplier_infos = supplier_info.search([('name', '=', obj.supplier.id)])
            products = product_category.search([('seller_ids', '=', [x.id for x in supplier_infos])])
            supplier_infos = supplier_info.search(
                [('product_tmpl_id', '=', [x.product_id.product_tmpl_id.id for x in products]),
                 ('name', '=', obj.supplier.id)])
            pricelist_partnerinfo = self.env['pricelist.partnerinfo']
            pricelist_partnerinfo_elmts = pricelist_partnerinfo.search(
                [('suppinfo_id', 'in', [x.id for x in supplier_infos])])

            fields = self.get_category_price_fields(category=category_name)
            product_pricelist_item = self.env['product.pricelist.item']
            product_pricelist_item_elmnts = product_pricelist_item.search([('price_version_id', '=', obj.pricelist.id)])
            if fields and pricelist_partnerinfo_elmts:
                for pricelist in product_pricelist_item_elmnts:
                    ws = wb.add_sheet(str(remove_wrong_characters(pricelist.name)), cell_overwrite_ok=True)
                    body += """
                    <table>
                    """
                    ws, body = self.write_prices(ws, fields, category_name, obj.start_date, obj.end_date,
                                                 obj.supplier.name,
                                                 pricelist_partnerinfo_elmts, pricelist, body)
                    body += """
                    </table>
                    """
                body += """
                </tbody>
                """
                body += final

                f = cStringIO.StringIO()
                f2 = cStringIO.StringIO()
                options = {
                    'page-size': 'Letter',
                    'margin-top': '0.75in',
                    'margin-right': '0.75in',
                    'margin-bottom': '0.75in',
                    'margin-left': '0.75in',
                    'encoding': "UTF-8",
                    'no-outline': None
                }
                pisa.pisaDocument(body.encode("ISO-8859-1"), f2)
                wb.save(f)
                obj.write({'excel_file': base64.encodestring(f.getvalue())})
                obj.write({'pdf_file': base64.encodestring(f2.getvalue())})
        return {
            'name': 'Export Prices',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'customer.price',
            'res_id': obj.id,
            'target': 'new'
        }

    # TODO: sort fields just for first index
    def get_category_price_fields(self, category):
        import importlib
        try:
            categ = importlib.import_module('openerp.addons.travel_' + category + '.' + category)
            category_fields = [x for x in CORE_FIELDS]
            if hasattr(categ, 'product_rate'):
                category_fields += [
                    (FIELD_TYPES[getattr(categ.product_rate, x).type], x, getattr(categ.product_rate, x).string)
                    for x in categ.product_rate.__dict__ if isinstance(getattr(categ.product_rate, x), fields.Field)]
                category_fields.sort()
            return category_fields
        except Exception, e:
            print e
            return []

    def write_prices(self, ws, _fields, category_name, start_date, end_date, supplier,
                     pricelist_partnerinfo_elmts, pricelist, body):

        style = xlwt.XFStyle()
        font = xlwt.Font()
        font.bold = True
        style.font = font
        elements = [_('Product'.upper()), _('Start Date'.upper()), _('End Date'.upper())]

        product_rate_supplement = self.env['product.rate.supplement']

        body += """
        <thead>
        <caption style=text-align=center; align=top><h1>""" + pricelist.name + """</h1>
        </caption>
        <tr>
        """
        for x in range(0, 3):
            ws.write(0, x, elements[x], style)
            body += """
            <th>
            """ + elements[x] + """</th>
            """
        count = 3
        if category_name.lower() == 'hotel':
            tmp_fields = []
            for x in _fields:
                if x[1].lower() == 'price':
                    tmp_fields.append((x[0] + 3, 'double', 'Double'))
                elif x[1].lower() not in ['simple', 'triple', 'start_date', 'end_date']:
                    tmp_fields.append((x[0] + 5, x[1], x[2]))
                elif x[1].lower() == 'simple':
                    tmp_fields.append((x[0] + 1, x[1], x[2]))
                elif x[1].lower() == 'triple':
                    tmp_fields.append((x[0] + 3, x[1], x[2]))
                else:
                    tmp_fields.append((x[0], x[1], x[2]))
            _fields = tmp_fields
        for x in sorted(_fields):
            if x[1].lower() != 'start_date' and x[1].lower() != 'end_date':
                ws.write(0, count, _(fix(str(x[1]).upper())), style)
                body += """
            <th>
            """ + _(fix(str(x[1]).upper())) + """</th>
            """
                count += 1
        if category_name.lower() == 'hotel':
            tmp_fields = []
            for x in _fields:
                if x[1].lower() == 'double':
                    tmp_fields.append((x[0], 'price', 'Price'))
                else:
                    tmp_fields.append((x[0], x[1], x[2]))
            _fields = tmp_fields
        non_repeated_supplemetes = []
        for partnerinfo in pricelist_partnerinfo_elmts:
            supplements = product_rate_supplement.search(
                [('suppinfo_id', '=', getattr(partnerinfo.suppinfo_id, 'id'))])
            for supplement in supplements:
                if supplement and start_date <= supplement.start_date <= end_date:
                    if supplement.supplement_id.id not in non_repeated_supplemetes:
                        non_repeated_supplemetes.append(supplement.supplement_id.id)
                        x = supplement.supplement_id.name
                        ws.write(0, count, _(fix(str(x).upper())), style)
                        body += """
            <th>
            """ + _(fix(str(x).upper())) + """</th>
            """
                    count += 1
        count = 1
        body += """
        </tr>
        </thead>
        <tbody>
        """
        for partnerinfo in pricelist_partnerinfo_elmts:
            if start_date <= partnerinfo.start_date <= end_date:
                ws.write(count, 0, str(partnerinfo.suppinfo_id.product_tmpl_id.name))
                ws.write(count, 1, str(partnerinfo.start_date))
                ws.write(count, 2, str(partnerinfo.end_date))
                body += """
                <tr>
                <td style="text-align=center;"> <span>""" + str(
                    partnerinfo.suppinfo_id.product_tmpl_id.name) + """</span></td> """ + """<td style="text-align=center;"><span>""" + str(
                    partnerinfo.start_date) + """</span></td> """ + """<td style="text-align=center;"><span>""" + str(
                    partnerinfo.end_date) + """</span></td> """
                res = self.get_customer_price(partnerinfo, pricelist, [f[1] for f in _fields], category_name.lower())
                second_count = 3
                for x in sorted(_fields):
                    if x[1].lower() != 'start_date' and x[1].lower() != 'end_date':
                        try:
                            ws.write(count, second_count, _(str(res[x[1]])))
                            body += """<td style="text-align=center;"><span>""" + _(
                                str(res[x[1]])) + """</span></td> """
                        except KeyError:
                            ws.write(count, second_count, _('Empty'))
                            body += """<td style="text-align=center;"><span>""" + _('Empty') + """</span></td> """
                        second_count += 1
                supplements = product_rate_supplement.search(
                    [('suppinfo_id', '=', getattr(partnerinfo.suppinfo_id, 'id'))])
                for supplement in supplements:
                    if supplement and start_date <= supplement.start_date <= end_date:
                        x = supplement.price
                        ws.write(count, second_count, _(str(x)))
                        body += """<td style="text-align=center;"><span>""" + _(
                            str(x)) + """</span></td> """
                        second_count += 1
                count += 1
                body += """
                 </tr>"""

        return ws, body

    # TODO: check currency
    def get_customer_price(self, partener_info, pricelist, fields, category):
        res = {'type': category}

        for field in fields:
            if category == 'hotel':
                if field in ['price', 'simple', 'triple']:
                    value = getattr(partener_info, field)

                    res_final = (value + pricelist.margin_per_pax) * (
                        1 + pricelist.price_discount) + pricelist.price_surcharge
                    res.update({field: res_final})
                else:
                    try:
                        attr = getattr(partener_info, field)
                        attr = getattr(attr, 'name')
                    except AttributeError:
                        try:
                            attr = getattr(partener_info.product_rate_id, field)
                        except AttributeError:
                            continue
                    res.update({field: attr})
            elif category in ['car', 'transfer', 'flight', 'package']:
                if field in ['price', 'child']:
                    value = getattr(partener_info, field)

                    res_final = (value + pricelist.margin_per_pax) * (
                        1 + pricelist.price_discount) + pricelist.price_surcharge
                    res.update({field: res_final})
                else:
                    try:
                        attr = getattr(partener_info, field)
                        attr = getattr(attr, 'name')
                    except AttributeError:
                        try:
                            attr = getattr(partener_info.product_rate_id, field)
                        except AttributeError:
                            continue
                    res.update({field: attr})
        return res
