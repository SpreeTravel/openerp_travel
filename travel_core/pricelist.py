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


from openerp.osv import fields, osv
from openerp.osv.orm import Model, TransientModel
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp

import time
import xlwt
import base64

FIELD_TYPES = {'date': 1, 'many2one': 2, 'float': 3, 'integer': 4}
CORE_FIELDS = [
    (1, 'start_date', 'Start Date'),
    (1, 'end_date', 'End Date'),
    (3, 'price', 'Price'),
    (3, 'child', 'Child')
]


class product_pricelist(Model):
    _name = 'product.pricelist'
    _inherit = 'product.pricelist'

    def _get_items(self, cr, uid, ids, fields, arg, context=None):
        res = {}
        for obj in self.browse(cr, uid, ids, context):
            res[obj.id] = [i.id for v in obj.version_id for i in v.items_id]
        return res

    def _get_version_id(self, cr, uid, oid, context=None):
        version_id = False
        version_obj = self.pool.get('product.pricelist.version')
        obj = self.browse(cr, uid, oid, context)
        if obj.version_id:
            version_id = obj.version_id[0].id
        else:
            version_vals = {
                'name': 'Default Version',
                'pricelist_id': obj.id,
                'active': True
            }
            version_id = version_obj.create(cr, uid, version_vals, context)
        return version_id

    def _set_items(self, cr, uid, oid, field, value, arg, context=None):
        ppi_obj = self.pool.get('product.pricelist.item')
        value = value or []
        for v in value:
            if v[0] == 0:
                version_id = self._get_version_id(cr, uid, oid, context)
                v[2].update({'price_version_id': version_id})
                ppi_obj.create(cr, uid, v[2], context)
            elif v[0] == 1:
                ppi_obj.write(cr, uid, v[1], v[2], context)
            elif v[0] == 2:
                ppi_obj.unlink(cr, uid, v[1], context)
        return True

    _columns = {
        'pricelist_item_ids': fields.function(_get_items, method=True,
                                            fnct_inv=_set_items,
                                            type='one2many', string='Items',
                                            relation='product.pricelist.item')
    }
    
    
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
            raise osv.except_osv(_('Warning!'), _("At least one pricelist has no active version !\nPlease create or activate one."))
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
            uom_price_already_computed = False
            results[product.id] = 0.0
            price = False
            rule_id = False
            for rule in items:
                if rule.min_quantity and qty<rule.min_quantity:
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
                                qty, False)], context=context)[product.id]
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
                    sinfo = supplierinfo_obj.search(cr, uid, [('product_tmpl_id', '=', product.product_tmpl_id.id)] + where)
                    price = 0.0
                    
                    if len(sinfo) > 0:                
                        for seller in product.seller_ids:
                            # I dont get this condition, what they meant
                            #if (not partner) or (seller.name.id != partner):
                            #    continue
                            if seller.id == sinfo[0]:
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
                                        #price = line.price
                                        price = product.price_get_partner(product.id, seller.id, params)
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
                            price_type.field, context=context)[product.id], round=False, context=context)

                if price is not False:
                    params = context.get('params', {})
                    paxs = self.pool.get('sale.order.line').get_total_paxs(cr, uid, params, context)
                    days = self.pool.get('sale.order.line').get_margin_days(cr, uid, params, context)
                    price_limit = price
                    price += days * paxs * (rule.margin_per_pax or 0.0)
                    price = price * (1.0+(rule.price_discount or 0.0))
                    if rule.price_round:
                        price = tools.float_round(price, precision_rounding=rule.price_round)
                    price += (rule.price_surcharge or 0.0)
                    if rule.price_min_margin:
                        price = max(price, price_limit+rule.price_min_margin)
                    if rule.price_max_margin:
                        price = min(price, price_limit+rule.price_max_margin)
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
            raise osv.except_osv(_('Warning!'),
                                 _("At least one pricelist has no active version !\nPlease create or activate one."))

        # product.product:
        product_ids = [i[0] for i in products_by_qty_by_partner]
        #products = dict([(item['id'], item) for item in product_obj.read(cr, uid, product_ids, ['categ_id', 'product_tmpl_id', 'uos_id', 'uom_id'])])
        products = product_obj.browse(cr, uid, product_ids, context=context)
        products_dict = dict([(item.id, item) for item in products])

        # product.category:
        product_category_ids = product_category_obj.search(cr, uid, [])
        product_categories = product_category_obj.read(cr, uid, product_category_ids, ['parent_id'])
        product_category_tree = dict([(item['id'], item['parent_id'][0]) for item in product_categories if item['parent_id']])

        results = {}
        for product_id, qty, partner in products_by_qty_by_partner:
            for pricelist_id in pricelist_ids:
                price = False

                tmpl_id = products_dict[product_id].product_tmpl_id and products_dict[product_id].product_tmpl_id.id or False

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
                                price = currency_obj.compute(cr, uid, ptype_src, res['currency_id'], price_tmp, round=False)
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
                                    price_type.field, context=context)[product_id], round=False, context=context)

                        params = context.get('params', {})
                        paxs = self.pool.get('sale.order.line').get_total_paxs(cr, uid, params, context)
                        days = self.pool.get('sale.order.line').get_margin_days(cr, uid, params, context)
                        if price is not False:
                            price_limit = price
                            price += days * paxs * (res['margin_per_pax'] or 0.0)
                            price = price * (1.0 + (res['price_discount'] or 0.0))
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

    _columns = {
        'margin_per_pax': fields.float('Margin per Pax',
                            digits_compute=dp.get_precision('Product Price')),
        'supplier_id': fields.many2one('res.partner', 'Supplier',
                                       domain=[('supplier', '=', True)])
    }


class customer_price(TransientModel):
    _name = 'customer.price'
    _columns = {
        'start_date': fields.date('Start date'),
        'end_date': fields.date('End date'),
        'file_price': fields.binary('File')
    }

    def export_prices(self, cr, uid, ids, context=None):
        wb = xlwt.Workbook()

        partner_obj = self.pool.get('res.partner')
        partner = partner_obj.browse(cr, uid, context['active_id'])
        pricelist = partner.property_product_pricelist

        category_obj = self.pool.get('product.category')
        category_ids = category_obj.search(cr, uid, [('type', '=', 'normal')],
                                           context=context)
        for categ in category_obj.browse(cr, uid, category_ids):
            name = categ.name
            fields = self.get_category_price_fields(name.lower())
            if fields:
                ws = wb.add_sheet(name, cell_overwrite_ok=True)
                self.write_prices(cr, uid, ws, fields, categ, pricelist, context)
        wb.save('/tmp/prices.xls')
        f = open('/tmp/prices.xls', 'r')
        obj = self.browse(cr, uid, ids[0], context)
        self.write(cr, uid, obj.id,
                   {'file_price': base64.encodestring(f.read())}, context)
        return {
            'name': 'Export Prices',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'customer.price',
            'res_id': obj.id,
            'target': 'new',
            'context': context
        }

    # TODO: sort fields just for first index
    def get_category_price_fields(self, category):
        import importlib
        try:
            categ = importlib.import_module('openerp.addons.travel_' + category + '.' + category)
            category_fields = [x for x in CORE_FIELDS]
            if hasattr(categ, 'product_rate'):
                category_fields += [(FIELD_TYPES[v._type], k, v.string) for k, v in categ.product_rate._columns.items()]
                category_fields.sort()
            return category_fields
        except:
            return []

    def write_prices(self, cr, uid, ws, fields, categ, pricelist, context=None):
        product_obj = self.pool.get('product.product')
        product_ids = product_obj.search(cr, uid, [('categ_id', '=', categ.id)],
                                         context=context)
        ws.write(0, 0, 'Product')
        x, y = 0, 1
        for f in fields:
            ws.write(x, y, f[2])
            y += 1
        x = 1
        for prod in product_obj.browse(cr, uid, product_ids):
            y = 0
            ws.write(x, y, prod.name)
            suppinfo = prod.seller_info_id
            if suppinfo:
                for pr in suppinfo.pricelist_ids:
                    y = 1
                    for f in fields:
                        if f[0] == 2:
                            value = getattr(pr, f[1]).name
                        elif f[0] == 3:
                            value = self.get_customer_price(cr, uid, pricelist,
                                                            prod, suppinfo,
                                                            getattr(pr, f[1]))
                        else:
                            value = getattr(pr, f[1])
                        ws.write(x, y, value)
                        y += 1
                    x += 1

    # TODO: check currency
    def get_customer_price(self, cr, uid, pricelist, prod, suppinfo, value):
        for rule in pricelist.pricelist_item_ids:
            if rule.categ_id and rule.categ_id.id != prod.categ_id.id:
                continue
            if rule.product_id and rule.product_id.id != prod.id:
                continue
            if rule.supplier_id and rule.supplier_id.id != suppinfo.name.id:
                continue
            value += (rule.margin_per_pax or 0.0)
            value = value * (1.0 + (rule.price_discount or 0.0))
            break
        return value
