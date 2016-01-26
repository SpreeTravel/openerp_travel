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
from openerp import fields, api
from openerp.models import Model


class res_partner(Model):
    _name = 'res.partner'
    _inherit = 'res.partner'

    @api.multi
    def set_conditions(self):
        import datetime
        if len(self):
            element = self[0]

            pool = self.env['customer.price']
            obj = pool.create({
                'pricelist': element.property_product_pricelist.id,
                'client': element.name,
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

    def _get_reservations(self, cr, uid, ids, fields, args, context=None):
        result = {}
        order_line = self.pool.get('sale.order.line')
        for obj in self.browse(cr, uid, ids, context):
            result[obj.id] = []
            to_search = [('start_date', '>=', dt.datetime.today())]
            if obj.customer:
                to_search.append(('customer_id', '=', obj.id))
            elif obj.supplier:
                to_search.append(('supplier_id', '=', obj.id))
            else:
                continue
            l_ids = order_line.search(cr, uid, to_search, context=context)
            result[obj.id] = l_ids
        return result

    reservation_ids = fields.Many2many(compute=_get_reservations, method=True,

                                       relation='sale.order.line',
                                       string='Reservations')
    pax = fields.Boolean('Pax')

    # TODO: poner el campo pax tambien en el formulario de partner

    @api.model
    def create(self, vals, context=None):
        context = context or {}
        if context.get('supplier', False):
            vals['supplier'] = True
        return super(res_partner, self).create(vals)

    _sql_constraints = [
        ('name_partner_unique', 'unique (name)',
         'The name of the partner must be unique !'),
    ]


class option_type(Model):
    _name = 'option.type'
    name = fields.Char('Name', size=64, translate=True)
    code = fields.Char('Code', size=32)
    option_value_ids = fields.One2many('option.value', 'option_type_id',
                                       'Option Values')


class option_value(Model):
    _name = 'option.value'
    name = fields.Char('Name', size=64, translate=True)
    code = fields.Char('Code', size=32)
    option_type_id = fields.Many2one('option.type', 'Option Type')

    def get_code_by_id(self, cr, uid, oid, context=None):
        return self.read(cr, uid, oid, ['code'], context)['code']

    def get_id_by_code(self, cr, uid, code, context=None):
        res = self.search(cr, uid, [('code', '=', code)], context=context)
        return res and res[0] or False


class destination(Model):
    _name = 'destination'
    code = fields.Char('Code', size=8)
    name = fields.Char('Name', size=128, required=True)
    description = fields.Text('Description')
    parent_id = fields.Many2one('destination', 'Parent')
    child_ids = fields.One2many('destination', 'parent_id', 'Children')


class destination_distance(Model):
    _name = 'destination.distance'
    origin = fields.Many2one('destinaon', 'Origin')
    target = fields.Many2one('destination', 'Target')
    distance = fields.Float('Distance')
