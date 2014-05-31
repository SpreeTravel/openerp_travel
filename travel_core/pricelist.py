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
from openerp.osv.orm import Model
from openerp.tools.translate import _

import time


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
                            params = context.get('params', {})
                            paxs = params.get('adults', 0) + params.get('children', 0)
                            if price and paxs > 0:
                                price = price * paxs
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
                            paxs = params.get('adults', 0) + params.get('children', 0)
                            if price and paxs > 0:
                                price = price * paxs

                        if price is not False:
                            price_limit = price
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
