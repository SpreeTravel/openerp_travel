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

from openerp.osv import fields
from openerp.osv.orm import TransientModel


class unique_product(TransientModel):
    _name = 'unique.product'
    _columns = {
        'unique_product_detail_ids': fields.one2many('unique.product.detail',
                                                     'unique_product_id',
                                                     'Products')
    }

    def get_final_id(self, cr, uid, model, obj, context=None):
        final_id = False
        for x in obj.unique_product_detail_ids:
            if x.final_product:
                to_search = [('product_id', '=', x.product_id.id)]
                final_id = model.search(cr, uid, to_search, context=context)[0]
                break
        return final_id

    # TODO: check sales for this product
    def unify(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0], context)
        model = self.pool.get(context['active_model'])
        final_id = self.get_final_id(cr, uid, model, obj, context)

        model_ids = context.get('active_ids', [])
        model_ids.remove(final_id)
        model.unlink(cr, uid, model_ids, context)
        return True

    def _get_products(self, cr, uid, context=None):
        model = self.pool.get(context['active_model'])
        model_ids = context.get('active_ids', [])
        detail_ids = []
        for x in model.browse(cr, uid, model_ids):
            detail_ids.append((0, 0, {'product_id': x.product_id.id}))
        return detail_ids

    _defaults = {
        'unique_product_detail_ids': _get_products
    }


class unique_product_detail(TransientModel):
    _name = 'unique.product.detail'
    _columns = {
        'product_id': fields.many2one('product.product', 'Product'),
        'final_product': fields.boolean('Final'),
        'unique_product_id': fields.many2one('unique.product', 'Unique')
    }
