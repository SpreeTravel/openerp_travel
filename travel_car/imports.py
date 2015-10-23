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

class import_car(TransientModel):
    _name = 'import.car'
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
            
            car = self.pool.get('product.car')
            supplier = self.pool.get('res.partner')
            supplierinfo = self.pool.get('product.supplierinfo')
            partnerinfo = self.pool.get('pricelist.partnerinfo')
            
            head = {sheet.cell_value(0, x): x for x in range(sheet.ncols)} 
            
            suppinfo_id = False
            car_name = ''
            car_id = False
            car_class_id = False
            transmission_id = False
            passengers = False
            price = False
            create = False
            for r in range(1, sheet.nrows):
            
                def cell(attr):
                    if sheet.cell(r, head[attr]).ctype == xlrd.XL_CELL_ERROR:
                        return None
                    return sheet.cell_value(r, head[attr])
                
                if cell('Supplier'):
                    supplier_name = cell('Supplier').upper()
                    supplier_ids = supplier.search(cr, uid, [('name', '=', supplier_name)])
                    if len(supplier_ids) > 1:
                        msg += 'Ambiguous Supplier name: ' + supplier_name + '\n'                        
                        supplier_id = False
                    elif len(supplier_ids) == 0:
                        msg += 'Supplier not found: ' + supplier_name + '\n'
                        supplier_id = False
                    else:
                        supplier_id = supplier_ids[0]
                    
                if cell('Car'):
                    car_name = cell('Car').upper()
                    car_ids = car.search(cr, uid, [('name', '=', car_name)])
                    if len(car_ids) > 1:
                        msg += 'Ambiguous car name: ' + car_name + '\n'                        
                        car_id = False
                    elif len(car_ids) == 0:
                        create = True
                        car_id = False
                    else:
                        car_id = car_ids[0]
                    
                if cell('Class'):
                    car_class = cell('Class').upper()
                    car_class_id = self.get_option_value(cr, uid, car_class, 'cl', {})
                    
                if cell('Transmission'):
                    transmission = cell('Transmission').upper()
                    transmission_id = self.get_option_value(cr, uid, transmission, 'tm', {})
                    
                if cell('Passengers'):
                    passengers = cell('Passengers')
     
                if cell('From'):
                    date_from = self.get_date(cell('From'))  
                    
                if cell('To'):
                    date_to = self.get_date(cell('To'))  
                    
                if cell('Price'):
                    price = cell('Price')
                else:
                    price = False
                    
                if create:
                    car_id = car.create(cr, uid, {'name': car_name,
                                                  'class_id': car_class_id,
                                                  'categ_id': 4,
                                                  'transmission_id': transmission_id,
                                                  'passengers': passengers})
                    create = False
 
                if supplier_id and car_id:
                    
                    suppinfo_id = None
                    product_tmpl_id = car.read(cr, uid, car_id, ['product_tmpl_id'])['product_tmpl_id'][0]
                    suppinfo_ids = supplierinfo.search(cr, uid, ['&', 
                                                                 ('name', '=', supplier_id), 
                                                                 ('product_tmpl_id', '=', product_tmpl_id)], 
                                                               context=context)
                    if len(suppinfo_ids) == 0:        
                        svals = {
                            'name': supplier_id,
                            'product_tmpl_id': product_tmpl_id,
                            'min_qty': 0
                        }
                        suppinfo_id = supplierinfo.create(cr, uid, svals, context)
                    else:
                        suppinfo_id = suppinfo_ids[0] 

                    pvals = {
                        'suppinfo_id': suppinfo_id,
                        'start_date': date_from,
                        'end_date': date_to,
                        'price': price,
                        'min_quantity': 0
                        }                 
                 
                    pricelist_ids = partnerinfo.search(cr, uid, [('suppinfo_id', '=', suppinfo_id), 
                                                                  ('start_date', '=', date_from), 
                                                                  ('end_date', '=', date_to)], 
                                                                 context=context)
                    if len(pricelist_ids) > 0:
                        partnerinfo.write(cr, uid, [pricelist_ids[0]], {'price': price}, 
                                                     context=context)                     
                    else:
                        partnerinfo.create(cr, uid, pvals, context)  
                        
            if msg == '':
                msg += '\n ================== \nRental information successfully uploaded. \n'
            else:
                msg += '\n ================== \nCheck that names are properly typed or present in the system. \n'
            
            msg += 'Press cancel to close'    
                    
            self.write(cr, uid, obj.id, {'result': msg}, context)
            return {
                'name': 'Import Rental Prices',
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'import.car',
                'res_id': obj.id,
                'target': 'new',
                'context': context,
            }
        else:
            raise osv.except_osv('Error!', 'You must select a file.')
                     
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
        
    def get_option_value(self, cr, uid, name, code, context=None):
        ot = self.pool.get('option.type')
        ov = self.pool.get('option.value')

        ot_id = ot.search(cr, uid, [('code', '=', code)], context=context)[0]
        to_search = [('name', '=', name), ('option_type_id', '=', ot_id)]
        ov_ids = ov.search(cr, uid, to_search, context=context)[0]
        return ov_ids
    
    