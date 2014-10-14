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

from openerp.osv import fields, osv
from openerp.osv.orm import Model
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF


class product_supplierinfo(Model):
    _name = 'product.supplierinfo'
    _inherit = 'product.supplierinfo'
    _columns = {
        'allotment_ids': fields.one2many('product.rate.allotment',
                                          'suppinfo_id',
                                          'Allotment')
    }


class product_rate_allotment(Model):
    _name = 'product.rate.allotment'
                
    def create(self, cr, uid, values, context=None):
        res = super(product_rate_allotment, self).create(cr, uid, values, context)
        #self.pool.get('allotment.state').calculate_allotment(cr, uid, context)              
        return res
    
    def write(self, cr, uid, ids, values, context=None):
        res = super(product_rate_allotment, self).write(cr, uid, ids, values, context)
        #self.pool.get('allotment.state').calculate_allotment(cr, uid, context)              
        return res
     
    def unlink(self, cr, uid, ids, context=None):
        daily_allotment = self.pool.get('allotment.state')
        suppinfo = self.pool.get('product.supplierinfo')   
        hotel = self.pool.get('product.hotel')
        for obj in self.browse(cr, uid, ids, context):  
            suppinfo_obj = suppinfo.browse(cr, uid, obj.suppinfo_id.id, context) 
            hotel_id = hotel.search(cr, uid, [('product_id', '=', suppinfo_obj.product_id.id)])                      
            daily_allotment_ids = daily_allotment.search(cr, uid, [('hotel_id', '=', hotel_id[0]),
                                                                   ('room_id', '=', obj.room_type_id.id),
                                                                   ('supplier_id', '=', suppinfo_obj.name.id),
                                                                   ('day', '>=', obj.start_date),
                                                                   ('day', '<=', obj.end_date)])
            daily_allotment.unlink(cr, uid, daily_allotment_ids, context)
            
        res = super(product_rate_allotment, self).unlink(cr, uid, ids, context)       
        return res   
    
    _columns = {
        'start_date': fields.date('Start date'),
        'end_date': fields.date('End date'),
        'suppinfo_id': fields.many2one('product.supplierinfo', 'Supplier'),
        'room_type_id': fields.many2one('option.value', 'Room',
                            domain="[('option_type_id.code', '=', 'rt')]"),
        'allotment': fields.integer('Allotment'),
        'release': fields.integer('Release')
    }
    
    _order = 'start_date asc'

class allotment_state(Model):
    _name = 'allotment.state'
    
    def _availability(self, cr, uid, ids, field, value, args, context=None):
        res = {}
        prod_allotment = self.pool.get('product.rate.allotment')
        suppinfo = self.pool.get('product.supplierinfo')
        for obj in self.browse(cr, uid, ids, context):        
            suppinfo_ids = suppinfo.search(cr, uid, [('name', '=', obj.supplier_id.id), 
                                                     ('product_id', '=', obj.hotel_id.product_id.id)], context)
            allotment_ids = prod_allotment.search(cr, uid, [('suppinfo_id', 'in', suppinfo_ids),
                                                            ('start_date', '<=', obj.day),
                                                            ('end_date', '>=', obj.day)], context)
            release = prod_allotment.browse(cr, uid, allotment_ids, context)[0].release
            difference = (dt.datetime.strptime(obj.day, DF) - dt.datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)).days
            if difference <= release:
                res[obj.id] = 0
            else: 
                res[obj.id] = max(0, obj.allotment - obj.reserved)
        return res

    def _reservations(self, cr, uid, uids, field_name, arg, context=None):
        res = {}
        order_line_model = self.pool.get('sale.order.line')
        
        for allotment in self.browse(cr, uid, uids, context=context):
            total_reserved = 0
            order_line_ids = order_line_model.search(cr, uid, [('product_id', '=', allotment.hotel_id.product_id.id),
                                                            ('start_date', '<=', allotment.day),
                                                            ('end_date', '>', allotment.day)])
            for line in order_line_model.browse(cr, uid, order_line_ids):
                for rooming in line.hotel_1_rooming_ids:
                    if rooming.room_type_id.id == allotment.room_id.id:
                        total_reserved += rooming.quantity
            res[allotment.id] = total_reserved
        return res
    
    def _get_allotment_from_order(self, cr, uid, ids, context=None):
        res = []
        order_lines = self.pool.get('sale.order.line').browse(cr, uid, ids, context=context)
        allotment_model = self.pool.get('allotment.state')
        hotel_model = self.pool.get('product.hotel')
        for ol in order_lines:
            if ol.category_id.name == 'Hotel':
                hotel_id = hotel_model.search(cr, uid, [('product_id', '=', ol.product_id.id)])[0]
                allotment_ids = allotment_model.search(cr, uid, [('hotel_id', '=', hotel_id), 
                                                      ('day', '>=', ol.start_date),
                                                      ('day', '<', ol.end_date)])
                res.extend(allotment_ids)
                
        return list(set(res))

    _columns = {
        'day': fields.date('Day'),
        'hotel_id': fields.many2one('product.hotel', 'Hotel'),
        'room_id': fields.many2one('option.value', 'Room',
                              domain="[('option_type_id.code', '=', 'rt')]"),
        'supplier_id': fields.many2one('res.partner', 'Supplier'),
        'allotment': fields.integer('Allotment'),
        'reserved': fields.function(_reservations, methdo=True, string='Reserved', type='integer',
                                    store = {'sale.order.line': (_get_allotment_from_order, [], 10)}),
        'available': fields.function(_availability, 
                                        string='Available', 
                                        type='integer'),
    }
    
    _order = 'day asc'
