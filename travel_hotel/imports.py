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
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################

import xlrd, datetime, base64, json

from openerp.osv import fields, osv
from openerp.osv.orm import TransientModel

class import_hotel(TransientModel):
    _name = 'import.hotel'
    _columns = {
        'file':
            fields.binary('File'),
        'result':
            fields.text('Result')
    }

    def import_file(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0], context)
        if obj.file:
            data = base64.decodestring(obj.file)
            msg = ' '
            document = xlrd.open_workbook(file_contents=data)
            
            for sheet in document.sheets():
                if sheet.nrows != 0:
                    new_msg = self.import_prices_data(cr, uid, sheet, context)
                    if new_msg != '':
                        msg += new_msg + '\n'
                    else:
                        msg += new_msg
                                                
            self.write(cr, uid, obj.id, {'result': msg}, context)
            return {
                'name': 'Import Prices',
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'import.hotel',
                'res_id': obj.id,
                'target': 'new',
                'context': context,
            }
        else:
            raise osv.except_osv('Error!', 'You must select a file.')

    def import_prices_data(self, cr, uid, sheet, context):
        
        msg = ''
        
        hotel                   = self.pool.get('product.hotel')
        product_product         = self.pool.get('product.product')
        partner                 = self.pool.get('res.partner')
        product_supplierinfo    = self.pool.get('product.supplierinfo')
        pricelist_partnerinfo   = self.pool.get('pricelist.partnerinfo')
        option_value            = self.pool.get('option.value')
        category                = self.pool.get('product.category')
        
        head = {sheet.cell_value(0, x): x for x in range(sheet.ncols)} 
        product_hotel = False
        hotel_info = ''
        supplier = False
        suppinfo_id = False
        meal_plan_id = False
        room_type_id = False
        date_from = False
        date_to = False
        child1 = False
        child2 = False
        double_value = False
        double_option = False
        simple_value = False
        simple_option = False
        triple_value = False
        triple_option = False
        
        for r in range(1, sheet.nrows):
            
            def cell(attr):
                if sheet.cell(r, head[attr]).ctype == xlrd.XL_CELL_ERROR:
                    return None
                return sheet.cell_value(r, head[attr])
                
            if cell('HOTEL NAME'):
                # insert additional information (room and hotel comments) of previous hotel
                if suppinfo_id:
                    product_supplierinfo.write(cr, uid, [suppinfo_id], {'info': hotel_info})
                    hotel_info = ''
                
                hotel_name = cell('HOTEL NAME').strip()
                category_id = category.search(cr, uid, [('name', '=', 'Hotel')])[0]
                product_hotel = hotel.search(cr, uid, [('name', '=', hotel_name)])
                if len(product_hotel) == 0:
                    msg += 'Hotel name not found: '+ hotel_name + '\n'
                    product_hotel = False
                elif len(product_hotel) > 1: 
                    msg += 'Ambiguous name for hotel: '+ hotel_name + '\n'
                    product_hotel = False
                else:
                    product_hotel = product_hotel[0]
                
            if cell('SUPPLIER'):
                if product_hotel:
                   suppinfo_id = None
                   supplier_name = str(cell('SUPPLIER')).strip()
                   if supplier_name != '':
                       partner_ids = partner.search(cr, uid, [('name', '=', supplier_name)])
                       if len(partner_ids) == 0:
                           msg += 'Supplier name not found: '+ supplier_name + '\n'
                       elif len(partner_ids) > 1: 
                           msg += 'Ambiguous name for supplier: '+ supplier_name + '\n'
                       else:
                           partner_id = partner_ids[0]
                           suppinfo_ids = product_supplierinfo.search(cr, uid, ['&', 
                                                                                ('name', '=', partner_id), 
                                                                                ('product_tmpl_id', '=', product_hotel.product_tmpl_id.id)], 
                                                                      context=context)
                           if len(suppinfo_ids) == 0:        
                               svals = {
                                   'name': partner_id,
                                   'product_tmpl_id': product_hotel.product_tmpl_id.id,
                                   'min_qty': 0
                               }
                               suppinfo_id = product_supplierinfo.create(cr, uid, svals, context)
                           else:
                               suppinfo_id = suppinfo_ids[0] 
                                                              
            if cell('MEAL PLAN'):
                meal_plan_id = cell('MEAL PLAN').strip()
                mp = option_value.get_id_by_code(cr, uid, 'mp', context)
                
            if cell('ROOM CATEGORY'):
                room_type_str = cell('ROOM CATEGORY').strip()
                room_type_id = option_value.get_id_by_code(cr, uid, 'rt', context)
                
            if cell('DATEBAND FROM'):
                date_from = self.get_date(cell('DATEBAND FROM'))
                double_value = False
                double_option = False
                simple_value = False
                simple_option = False
                triple_value = False
                triple_option = False
                
            if cell('DATEBAND TO'):
                date_to = self.get_date(cell('DATEBAND TO'))  
        
            if cell('ROOM TYPE'):
                if cell('ROOM TYPE') == 'C1':
                    child1 = cell('NET RATE')
                elif cell('ROOM TYPE') == 'C2':
                    child2 = cell('NET RATE')                       
                elif cell('ROOM TYPE') == 'D':
                    double_value = self.get_float(cell('NET RATE'))
                    double_option = True
                elif cell('ROOM TYPE') == 'S':
                    simple_value = self.get_float(cell('NET RATE'))
                    simple_option = True                    
                elif cell('ROOM TYPE') == 'T':
                    triple_value = self.get_float(cell('NET RATE'))
                    triple_option = True    
            
            if cell('HOTEL COMMENTS') and cell('HOTEL COMMENTS').strip() != '':
                hotel_info = cell('HOTEL COMMENTS') + '\n\n' + hotel_info 
                                
            if cell('ROOM COMMENTS') and cell('ROOM COMMENTS').strip() != '':
                #hotel_info += option_value.get_code_by_id(cr, uid, room_type_id) + '\n' 
                hotel_info += cell('ROOM COMMENTS') + '\n\n' 
            
            if simple_option and double_option and triple_option and product_hotel and suppinfo_id:
                 pvals = {
                    'suppinfo_id': suppinfo_id,
                    'start_date': date_from,
                    'end_date': date_to,
                    'room_type_id': room_type_id,
                    'meal_plan_id': mp,
                    'price': double_value,
                    'simple': simple_value,
                    'triple': triple_value,
                    'child': child1,
                    'second_child': child2,
                    'min_quantity': 0
                 }                 
                 
                 pricelist_ids = pricelist_partnerinfo.search(cr, uid, [('suppinfo_id', '=', suppinfo_id), 
                                                                       ('start_date', '=', date_from), 
                                                                       ('end_date', '=', date_to), 
                                                                       ('room_type_id', '=', room_type_id),
                                                                       ('meal_plan_id', '=', mp)], 
                                                             context=context)
                 if len(pricelist_ids) > 0:
                     pricelist_partnerinfo.write(cr, uid, [pricelist_ids[0]], {'price': double_value, 
                                                                           'simple': simple_value,
                                                                           'triple': triple_value,
                                                                           'child': child1,
                                                                           'second_child': child2}, 
                                                 context=context)                     
                 else:
                     pricelist_partnerinfo.create(cr, uid, pvals, context)
                     
           
        # insert additional information (room and hotel comments) of previous hotel
        # last hotel in sheet case
        if suppinfo_id:
            product_supplierinfo.write(cr, uid, [suppinfo_id], {'info': hotel_info})
            hotel_info = ''       
                
        return msg
            
    def get_date(self, value):
        try:
            d = BASE_DATE + int(value)
            return datetime.datetime.fromordinal(d)
        except:
            return datetime.datetime(2017, 1, 1)

    def get_float(self, value):
        try:
            return float(value)
        except:
            return 0.0
        