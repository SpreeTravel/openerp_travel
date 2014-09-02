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
    _columns = {
        'start_date': fields.date('Start date'),
        'end_date': fields.date('End date'),
        'suppinfo_id': fields.many2one('product.supplierinfo', 'Supplier'),
        'room_type_id': fields.many2one('option.value', 'Room',
                            domain="[('option_type_id.code', '=', 'rt')]"),
        'allotment': fields.integer('Allotment'),
        'release': fields.integer('Release')
    }


class allotment_state(Model):
    _name = 'allotment.state'
    _columns = {
        'day': fields.date('Day'),
        'hotel_id': fields.many2one('product.hotel', 'Hotel'),
        'room_id': fields.many2one('option.value', 'Room',
                              domain="[('option_type_id.code', '=', 'rt')]"),
        'supplier_id': fields.many2one('res.partner', 'Supplier'),
        'allotment': fields.integer('Allotment'),
        'reserved': fields.integer('Reserved'),
        'available': fields.integer('Available'),
    }

    # TODO: incluir el chequeo del release
    def calculate_allotment(self, cr, uid, context=None):
        hotel_obj = self.pool.get('product.hotel')
        hotel_ids = hotel_obj.search(cr, uid, [], context=context)

        line_obj = self.pool.get('sale.order.line')

        for hotel in hotel_obj.browse(cr, uid, hotel_ids):
            for supinfo in hotel.seller_ids:
                for allotment in supinfo.allotment_ids:
                    start_date = dt.datetime.strptime(allotment.start_date, DF)
                    end_date = dt.datetime.strptime(allotment.end_date, DF)

                    current_date = start_date
                    while(current_date < end_date):
                        vals = {}
                        vals['day'] = current_date
                        vals['hotel_id'] = hotel.id
                        vals['room_id'] = allotment.room_type_id.id
                        vals['supplier_id'] = supinfo.name.id
                        vals['allotment'] = allotment.allotment

                        to_search_allotment = [(k, '=', v) for k, v in vals.items()]
                        allotment_id = self.search(cr, uid, to_search_allotment, context=context)

                        vals['reserved'] = 0
                        to_search_line = [
                            ('product_id', '=', hotel.product_id.id),
                            ('start_date', '<=', current_date),
                            ('end_date', '>=', current_date),
                            ('supplier_id', '=', supinfo.name.id),
                            ('state', 'not in', ['draft', 'cancel'])
                        ]
                        line_ids = line_obj.search(cr, uid, to_search_line)
                        for line in line_obj.browse(cr, uid, line_ids):
                            for rooming in line.hotel_1_rooming_ids:
                                if rooming.room_type_id.id == allotment.room_type_id.id:
                                    vals['reserved'] += rooming.quantity

                        vals['available'] = allotment.allotment - vals['reserved']
                        if vals['available'] < 0:
                            raise osv.except_osv('Error!',
                                                 "No room available in allotment.")
                        if allotment_id:
                            self.write(cr, uid, allotment_id[0],
                                       {'reserved': vals['reserved'],
                                        'available': vals['available']})
                        else:
                            self.create(cr, uid, vals)
                        current_date = current_date + dt.timedelta(1)
