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

from openerp.osv import fields
from openerp.osv.orm import Model


class sale_context(Model):
    _name = 'sale.context'
    _inherit = 'sale.context'
    _columns = {
        'hotel_1_rooming_ids': fields.one2many('sale.rooming', 'sale_context_id',
                                               'Rooming'),
        'hotel_2_meal_plan_id': fields.many2one('option.value', 'Plan',
                            domain="[('option_type_id.code', '=', 'mp')]")
    }

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
        self.set_paxs_for_hotel(cr, uid, obj, context)
        return res

    def write(self, cr, uid, ids, vals, context=None):
        res = super(sale_order_line, self).write(cr, uid, ids, vals, context)
        for obj in self.browse(cr, uid, ids, context):
            self.set_paxs_for_hotel(cr, uid, obj, context)
        return res

    def set_paxs_for_hotel(self, cr, uid, obj, context=None):
        adults, children = 0, 0
        for x in obj.hotel_1_rooming_ids:
            adults += x.adults * x.quantity
            children += x.children * x.quantity
        cr.execute('update sale_context set adults=%s, children=%s where id=%s', (adults, children, obj.sale_context_id.id))
        return True
