# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010, 2013, 2014 Tiny SPRL (<http://tiny.be>).
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

import simplejson
from lxml import etree

from openerp import fields, api
from openerp.models import Model


class sale_order(Model):
    _name = 'sale.order'
    _inherit = 'sale.order'

    @api.one
    def copy(self):
        res = super(sale_order, self).copy()
        category_table = self.env['product.category']
        category = category_table.search([('name', '=', 'Hotel')])
        for ol in self.order_line:
            if ol.category_id.id == category.id:
                vals = []
                for rooming in ol.hotel_1_rooming_ids:
                    vals.append([0, False, {
                        'id': rooming.id,
                        'room_type_id': rooming.room_type_id,
                        'quantity': rooming.quantity,
                        'children': rooming.children,
                        'room': rooming.room,
                        'adults': rooming.adults
                    }])
                for x in res.order_line:
                    if x.category_id.id == category.id and x.product_id.id == ol.product_id.id and x.start_date == ol.start_date and x.end_date == ol.end_date:
                        x.update({'hotel_1_rooming_ids': vals})
        return res


class sale_context(Model):
    _name = 'sale.context'
    _inherit = 'sale.context'

    hotel_1_rooming_ids = fields.One2many('sale.rooming', 'sale_context_id',
                                          'Rooming')
    hotel_2_meal_plan_id = fields.Many2one('option.value', 'Plan',
                                           domain="[('option_type_id.code', '=', 'mp')]")

    def update_view_with_context_fields(self, cr, uid, res, context=None):
        res = super(sale_context, self).update_view_with_context_fields(cr, uid, res, context)
        modifiers = {'invisible': [('category', '=', 'hotel')]}
        doc = etree.XML(res['arch'])
        try:
            gp = doc.xpath("//group[@name='paxs_fields']")[0]
            gp.set('modifiers', simplejson.dumps(modifiers))
            res['arch'] = etree.tostring(doc)
        except:
            pass
        return res


class sale_order_line(Model):
    _name = 'sale.order.line'
    _inherit = 'sale.order.line'

    def create(self, cr, uid, vals, context=None):
        res = super(sale_order_line, self).create(cr, uid, vals, context)
        obj = self.browse(cr, uid, res, context)
        if obj.category == 'hotel':
            self.set_paxs_for_hotel(cr, uid, obj, context)
        return res

    def write(self, cr, uid, ids, vals, context=None):
        res = super(sale_order_line, self).write(cr, uid, ids, vals, context)
        for obj in self.browse(cr, uid, ids, context):
            if obj.category == 'hotel':
                self.set_paxs_for_hotel(cr, uid, obj, context)
        return res

    def set_paxs_for_hotel(self, cr, uid, obj, context=None):
        adults, children = 0, 0
        for x in obj.hotel_1_rooming_ids:
            adults += x.adults * x.quantity
            children += x.children * x.quantity
        cr.execute('update sale_context set adults=%s, children=%s where id=%s',
                   (adults, children, obj.sale_context_id.id))
        return True

    def get_total_paxs(self, cr, uid, params, context=None):
        if params.get('category', False) == 'hotel':
            occupation = params.get('hotel_1_rooming_ids', [])
            return self.pool.get('sale.rooming').get_total_paxs(cr, uid, occupation, context)
        return params.get('adults', 0) + params.get('children', 0)

    def get_margin_days(self, cr, uid, params, context=None):
        '''
        The number of days of the service countable for apply a per day margin.
        Redefining the travel_core function
        '''
        return super(sale_order_line, self).get_margin_days(cr, uid, params, context) - 1
