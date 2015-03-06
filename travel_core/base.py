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

import datetime as dt

from openerp.osv import fields
from openerp.osv.orm import Model


class res_partner(Model):
    _name = 'res.partner'
    _inherit = 'res.partner'

    def _get_reservations(self, cr, uid, ids, fields, args, context=None):
        result = {}
        order_line = self.pool.get('sale.order.line')
        for obj in self.browse(cr, uid, ids, context):
            result[obj.id] = []
            to_search = [('start_date', '>=', dt.datetime.today())]
            if obj.customer == True:
                to_search.append(('customer_id', '=', obj.id))
            elif obj.supplier == True:
                to_search.append(('supplier_id', '=', obj.id))
            else:
                continue
            l_ids = order_line.search(cr, uid, to_search, context=context)
            result[obj.id] = l_ids
        return result

    _columns = {
        'reservation_ids': fields.function(_get_reservations, method=True,
                                           type='many2many',
                                           relation='sale.order.line',
                                           string='Reservations'),
        'pax': fields.boolean('Pax'),
        # TODO: poner el campo pax tambien en el formulario de partner
    }

    def create(self, cr, uid, vals, context=None):
        context = context or {}
        if context.get('supplier', False):
            vals['supplier'] = True
        return super(res_partner, self).create(cr, uid, vals, context)

    _sql_constraints = [
        ('name_partner_unique', 'unique (name)',
         'The name of the partner must be unique !'),
    ]


class option_type(Model):
    _name = 'option.type'
    _columns = {
        'name': fields.char('Name', size=64, translate=True),
        'code': fields.char('Code', size=32),
        'option_value_ids': fields.one2many('option.value', 'option_type_id',
                                            'Option Values')
    }


class option_value(Model):
    _name = 'option.value'
    _columns = {
        'name': fields.char('Name', size=64, translate=True),
        'code': fields.char('Code', size=32),
        'option_type_id': fields.many2one('option.type', 'Option Type')
    }

    def get_code_by_id(self, cr, uid, oid, context=None):
        return self.read(cr, uid, oid, ['code'], context)['code']

    def get_id_by_code(self, cr, uid, code, context=None):
        res = self.search(cr, uid, [('code', '=', code)], context=context)
        return res and res[0] or False
    
class destination(Model):
    _name = 'destination'
    _columns = {
        'code': fields.char('Code', size=8),
        'name': fields.char('Name', size=128, required=True),
        'description': fields.text('Description'),
        'parent_id': fields.many2one('destination', 'Parent'),
        'child_ids': fields.one2many('destination', 'parent_id', 'Children')
    }


class destination_distance(Model):
    _name = 'destination.distance'
    _columns = {
        'origin': fields.many2one('destination', 'Origin'),
        'target': fields.many2one('destination', 'Target'),
        'distance': fields.float('Distance')
    }
