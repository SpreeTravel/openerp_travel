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
                                                     'Products'),
        'product_ids': fields.char('Products', size=255)
    }

    def unify(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0], context)
        model = self.pool.get(context['active_model'])
        model_ids = context.get('active_ids', [])

        vals = {}
        for x in obj.unique_product_detail_ids:
            attr = x.product_field_id
            if attr.ttype == 'many2one':
                vals[attr.name] = getattr(x.product_id, attr.name).id
            elif attr.ttype == 'one2many':
                pass
            elif attr.ttype == 'many2many':
                pass
            else:
                vals[attr.name] = getattr(x.product_id, attr.name)
        model_id = model.create(cr, uid, vals, context)

        model.unlink(cr, uid, model_ids, context)
        return True

    def _get_products(self, cr, uid, context=None):
        model = self.pool.get(context['active_model'])
        model_ids = context.get('active_ids', [])
        product_ids = [x.product_id.id for x in model.browse(cr, uid, model_ids)]
        models = ['product.template', 'product.product', context['active_model']]
        model_fields = self.pool.get('ir.model.fields')
        field_ids = model_fields.search(cr, uid, [('model', 'in', models)],
                                        context=context)
        detail_ids = []
        for f in field_ids:
            detail_ids.append((0, 0, {'product_field_id': f,
                                      'product_id': product_ids[0]}
                               ))
        return detail_ids

    _defaults = {
        'unique_product_detail_ids': _get_products
    }


class unique_product_detail(TransientModel):
    _name = 'unique.product.detail'
    _columns = {
        'product_field_id': fields.many2one('ir.model.fields', 'Field'),
        'product_id': fields.many2one('product.product', 'Product'),
        'unique_product_id': fields.many2one('unique.product', 'Unique')
    }
