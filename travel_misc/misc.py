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
from openerp.osv.orm import Model, TransientModel


class product_misc(Model):
    _name = 'product.misc'
    _inherits = {'product.product': 'product_id'}
    _inherit = ['mail.thread']
    _columns = {
        'product_id': fields.many2one('product.product', 'Product',
                                      required=True, ondelete="cascade"),
        'misc_name': fields.related('product_id', 'name', type='char',
                                      string='Name', size=128, select=True,
                                      store=True),
    }

    _order = 'misc_name asc'

    def price_get_partner(self, cr, uid, cls, to_search, params, context=None):
        price = 0.0
        model = self.pool.get(cls)
        adults = params.get('adults', 0)
        children = params.get('children', 0)
        pp_ids = model.search(cr, uid, to_search, context=context)
        if pp_ids:
            pp = model.browse(cr, uid, pp_ids[0], context)
            price = pp.price * adults + pp.price + children
        return price


class product_category_change(TransientModel):
    _name = 'product.category.change'
    _columns = {
        'category_id': fields.many2one('product.category', 'Category')
    }

    def convert(self, cr, uid, ids, context=None):
        prod = self.pool.get('product.product')
        misc = self.pool.get('product.misc')
        obj = self.browse(cr, uid, ids[0], context)
        model = 'product.' + obj.category_id.name.lower()
        product_ids = context.get('active_ids', [])
        for p in misc.browse(cr, uid, product_ids, context):
            to_search = [
                ('name', '=', p.name),
                ('categ_id', '=', obj.category_id.id)
            ]
            p_ids = prod.search(cr, uid, to_search, context=context)
            if p_ids:
                pass
            to_create = {x[0]: x[2] for x in to_search}
            self.pool.get(model).create(cr, uid, to_create, context)
        misc.unlink(cr, uid, product_ids, context)
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'product.misc',
            'view_type': 'form',
            'view_mode': 'tree,form',
        }
