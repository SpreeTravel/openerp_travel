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
from openerp.osv.orm import Model


class sale_rooming(Model):
    _name = 'sale.rooming'

    def _load_default_room_value(self, cr, uid, context=None):
        ctx = dict(context or {})
        room_value = self.pool.get('option.value').search(cr, uid, [('load_default', '=', 'True')], context=ctx)
        if room_value:
            return room_value[0]
        return self.pool.get('option.value').search(cr, uid, [], context=ctx)

    _columns = {
        'room': fields.selection([('simple', 'Single'),
                                  ('double', 'Double'),
                                  ('triple', 'Triple')], 'Room'),
        'adults': fields.integer('Adults'),
        'children': fields.integer('Children'),
        'quantity': fields.integer('Qty'),
        'room_type_id': fields.many2one('option.value', 'Room',
                                domain="[('option_type_id.code', '=', 'rt')]"),
        'sale_context_id': fields.many2one('sale.context', 'Context')
    }

    def onchange_room(self, cr, uid, ids, room, context=None):
        rooms = ['simple', 'double', 'triple']
        return {'value': {'adults': rooms.index(room) + 1}}

    def onchange_adults(self, cr, uid, ids, adults, context=None):
        rooms = ['simple', 'double', 'triple']
        if adults > 3:
            return {
                'value': {'adults': 2},
                'warning': {
                    'title': 'Error!',
                    'message': 'The adults quantity must be lower than 3.'
                }
            }
        else:
            return {'value': {'room': rooms[adults - 1]}}

    def extract_values(self, cr, uid, occupation, context=None):
        result = []
        for o in occupation:
            adults = 0
            children = 0
            room = None
            room_type_id = False
            quantity = 0
            if o[0] == 0:
                adults = int(o[2].get('adults', 0))
                children = int(o[2].get('children', 0))
                quantity = o[2].get('quantity', 1)
                room = o[2].get('room', 'double')
                room_type_id = o[2].get('room_type_id', False)
            elif o[0] == 1:
                if o[2].get('adults', False):
                    adults = int(o[2]['adults'])
                else:
                    obj = self.browse(cr, uid, o[1], context)
                    if obj.adults:
                        adults = obj.adults
                if o[2].get('children', False):
                    children = int(o[2]['children'])
                else:
                    obj = self.browse(cr, uid, o[1], context)
                    if obj.children:
                        children = obj.children
                if o[2].get('quantity', False):
                    quantity = o[2]['quantity']
                else:
                    obj = self.browse(cr, uid, o[1], context)
                    quantity = obj.quantity
                if o[2].get('room', False):
                    room = o[2]['room']
                else:
                    obj = self.browse(cr, uid, o[1], context)
                    room = obj.room
                if o[2].get('room_type_id', False):
                    room_type_id = o[2]['room_type_id']
                else:
                    obj = self.browse(cr, uid, o[1], context)
                    room_type_id = obj.room_type_id.id
            elif o[0] == 4:
                obj = self.browse(cr, uid, o[1], context)
                if obj.adults:
                    adults = obj.adults
                if obj.children:
                    children = obj.children
                quantity = obj.quantity
                room = obj.room
                if obj.room_type_id:
                    room_type_id = obj.room_type_id.id
            result.append({'room': room,
                           'adults': adults,
                           'children': children,
                           'quantity': quantity,
                           'room_type_id': room_type_id})
        return result

    def get_total_paxs(self, cr, uid, occupation, context=None):
        result = self.extract_values(cr, uid, occupation, context)
        adults = 0
        children = 0
        for r in result:
            adults += r['adults'] * r['quantity']
            children += r['children'] * r['quantity']
        return adults + children

    _defaults = {
        'room': 'double',
        'adults': 2,
        'quantity': 1,
        'room_type_id': _load_default_room_value
    }
    
class option_value(Model):
    _name = 'option.value'
    _inherit = 'option.value'
    
    def _name_search(self, cr, user, name='', args=None, operator='ilike', context=None, limit=100, name_get_uid=None):
        if context.get('name_search_product_id', False):
            product_model   = self.pool.get('product.product')
            product_tmpl_id = product_model.browse(cr, user, context['name_search_product_id'], context).product_tmpl_id.id
            suppinfo_model  = self.pool.get('product.supplierinfo')
            domain = [('product_tmpl_id', '=', product_tmpl_id)]
            if context.get('name_search_supplier_id', False):
                domain += [('name', '=', context['name_search_supplier_id'])]
            suppinfo_ids    = suppinfo_model.search(cr, user, domain, context=context)
            room_type_ids = []
            for suppinfo_id in suppinfo_ids:
                pricelist_model  = self.pool.get('pricelist.partnerinfo')
                pricelist_ids = pricelist_model.search(cr, user, [('suppinfo_id', '=', suppinfo_id)], context=context)
                room_type_ids = list(set([p.room_type_id.id for p in pricelist_model.browse(cr, user, pricelist_ids, context=context)]))
            args += [('id', 'in', room_type_ids)]                
        return super(option_value, self)._name_search(cr, user, name, args, operator, context, limit, name_get_uid)
    
    
    
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
    
    
    
    
    
        
