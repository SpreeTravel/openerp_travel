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

import xlrd, base64, datetime, timeit

from openerp.osv import fields, osv
from openerp.osv.orm import TransientModel

BASE_DATE = 693594

class import_allotment(TransientModel):
    _name = 'import.allotment'
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

            msg = ''
            document = xlrd.open_workbook(file_contents=data)
            sheet = document.sheets()[0]
            
            hotel = self.pool.get('product.hotel')
            allotment_model = self.pool.get('product.rate.allotment')
            daily_allotment_model = self.pool.get('allotment.state')
            supplierinfo = self.pool.get('product.supplierinfo')
            
            head = {sheet.cell_value(0, x): x for x in range(sheet.ncols)} 
            
            hotel_id = False
            room_type_id = False
            date_from = False
            date_to = False
            allotment = False
            release = False
            for r in range(1, sheet.nrows):
            
                def cell(attr):
                    if sheet.cell(r, head[attr]).ctype == xlrd.XL_CELL_ERROR:
                        return None
                    return sheet.cell_value(r, head[attr])
                
                if cell('Hotel'):
                    hotel_name = cell('Hotel').upper()
                    hotel_ids = hotel.search(cr, uid, [('name', '=', hotel_name)])
                    if len(hotel_ids) > 1:
                        msg += 'Ambiguous Hotel name: ' + hotel_name + '\n'                        
                        hotel_id = False
                    elif len(hotel_ids) == 0:
                        msg += 'Hotel not found: ' + hotel_name + '\n'
                        hotel_id = False
                    else:
                        hotel_id = hotel_ids[0]
                        print 'Updating ' +hotel_name+ ' allotments\n'
                    
                if cell('Room type'):
                    room_type_str = cell('Room type').strip().upper()
                    room_type_ids = self.get_option_value(cr, uid, room_type_str, 'rt', context)
                    if len(room_type_ids) > 1:
                        msg += 'Ambiguous Room type : ' + room_type_str + '\n'
                        room_type_id = False
                    elif len(room_type_ids) == 0:
                        msg += 'Room type not found: ' + room_type_str + '\n'
                        room_type_id = False
                    else:
                        room_type_id = room_type_ids[0]
                        
                if cell('From'):
                    date_from = self.get_date(cell('From'))  
                    
                if cell('To'):
                    date_to = self.get_date(cell('To'))  
                    
                if cell('Allotment'):
                    allotment = cell('Allotment')
                else:
                    allotment = False
                    
                if cell('Release'):
                    release = cell('Release')
                else:
                    release = False
                    
                if hotel_id and room_type_id and date_from and date_to and allotment != False and release != False:
                    product_id = hotel.read(cr, uid, hotel_id, ['product_tmpl_id'], context)
                    suppinfo_ids = supplierinfo.search(cr, uid, 
                                                       [('product_tmpl_id', '=', product_id['product_tmpl_id'][0])], 
                                                       context=context)
                    if len(suppinfo_ids) > 1:
                        msg += 'More than one supplier for hotel: ' +hotel_name+ '\n'
                    elif len(suppinfo_ids) == 0:
                        msg += 'No supplier_info found ' +hotel_name+ ' \n'
                    else:
                        allotment_ids = allotment_model.search(cr, uid, [('suppinfo_id', '=', suppinfo_ids[0]),
                                                                         ('room_type_id', '=', room_type_id),
                                                                         ('start_date', '=', date_from),
                                                                         ('end_date', '=', date_to)])
                        vals = {
                                'start_date': date_from,
                                'end_date': date_to,
                                'suppinfo_id': suppinfo_ids[0],
                                'room_type_id': room_type_id,
                                'allotment': allotment,
                                'release': release
                        }
                        if len(allotment_ids) > 1:
                            msg += 'Duplicated Allotments for hotel:' +hotel_name+ '\n'
                        elif len(allotment_ids) == 1:
                            allotment_model.write(cr, uid, allotment_ids, vals)
                        else:
                            allotment_model.create(cr, uid, vals)
            
            if msg == '':
                msg += '\n ================== \Allotment successfully uploaded. \n'
            else:
                msg += '\n ================== \nCheck that names are properly typed or present in the system. \n'
            
            msg += 'Press cancel to close'    
                    
            self.write(cr, uid, obj.id, {'result': msg}, context)
            return {
                'name': 'Import Allotment',
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'import.allotment',
                'res_id': obj.id,
                'target': 'new',
                'context': context,
            }
        else:
            raise osv.except_osv('Error!', 'You must select a file.')
                     
    def get_date(self, value):
        return datetime.datetime.strptime(value, '%d.%m.%y')

    def get_float(self, value):
        try:
            return float(value)
        except:
            return 0.0     
        
    def get_option_value(self, cr, uid, name, code, context=None):
        ot = self.pool.get('option.type')
        ov = self.pool.get('option.value')

        ot_id = ot.search(cr, uid, [('code', '=', code)], context=context)[0]
        to_search = [('name', '=', name), ('option_type_id', '=', ot_id)]
        ov_ids = ov.search(cr, uid, to_search, context=context)
        return ov_ids
    
    