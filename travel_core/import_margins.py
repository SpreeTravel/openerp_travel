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

import xlrd, base64, datetime

from openerp.osv import fields, osv
from openerp.osv.orm import TransientModel

BASE_DATE = 693594

class import_margins(TransientModel):
    _name = 'import.margins'
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
            #try:
            msg = ''
            document = xlrd.open_workbook(file_contents=data)
            sheet = document.sheets()[-1]
            
            season_name = sheet.name
            
            product = self.pool.get('product.product')
            pricelist = self.pool.get('product.pricelist')
            rule = self.pool.get('product.pricelist.item')
            version = self.pool.get('product.pricelist.version')
            currency = self.pool.get('res.currency')
            customer = self.pool.get('res.partner')
            
            pub_pricelist_id = pricelist.search(cr, uid, [('name', '=', 'Public Pricelist')])[0]
            
            gbp_id = currency.search(cr, uid, [('name', '=', 'GBP')])[0]
            
            date_start = self.get_date(sheet.cell_value(0, 3))            
            date_end   = self.get_date(sheet.cell_value(0, 5))
            
            first_col = 3

            for col in range(first_col, sheet.ncols): 
                
                customer_name = sheet.cell_value(1, col).upper()
                customer_ids = customer.search(cr, uid, [('name', '=', customer_name)])
                if customer_ids:
                    customer_obj = customer.browse(cr, uid, customer_ids, context)[0]
                else:
                    if first_col == col:
                        msg += 'Customer: ' + customer_name + ' not found in the system \n'
                    continue
                                    
                curr_str = sheet.cell_value(2, col)
                if curr_str:
                    curr_id = currency.search(cr, uid, [('name', '=', curr_str.upper())])[0]
                else:
                    curr_id = gbp_id
                xrate = sheet.cell_value(3, col)
                if not xrate:
                    xrate = 1.0                    
                     
                pricelist_obj = customer_obj.property_product_pricelist
                pricelist_id = customer_obj.property_product_pricelist.id
                pricelist_name = customer_obj.property_product_pricelist.name
                if pricelist_name == 'Public Pricelist':
                    pricelist_id = pricelist.create(cr, uid, {'name': customer_name + ' Pricelist',
                                               'currency_id': curr_id,
                                               'type': 'sale'})
                
                customer_obj.write({'property_product_pricelist': pricelist_id})
                    
                version_ids = version.search(cr, uid, [('pricelist_id', '=', pricelist_id), 
                                                      ('date_start', '=', date_start),
                                                      ('date_end', '=', date_end)])
                
                if version_ids:
                    version_id = version_ids[0]
                else:
                    version_id = version.create(cr, uid, {'name': season_name,
                                                          'date_start': date_start,
                                                          'date_end': date_end,
                                                          'pricelist_id': pricelist_id})
      
                for row in range(4, sheet.nrows):
                    hotel_name = sheet.cell_value(row, 1).upper()
                    product_ids = product.search(cr, uid, [('name', '=', hotel_name)])
                    if not product_ids:
                        if first_col == col:
                            msg += 'Hotel: ' + hotel_name + ' not found in the system \n'
                    elif len(product_ids) > 1:
                        if first_col == col:
                            msg += 'Hotel: ' + hotel_name + ' not unique in the system \n'
                    else:
                        raw_margin = sheet.cell_value(row, col)
                        if isinstance(raw_margin, float):
                            try:
                                margin = raw_margin*xrate
                            except:
                                pass
                            rule_ids = rule.search(cr, uid, [('product_id', '=', product_ids[0]), 
                                                             ('price_version_id', '=', version_id)])
                            if rule_ids:
                                rule.write(cr, uid, rule_ids, {'margin_per_pax': margin})
                            else:
                                rule.create(cr, uid, {'price_version_id': version_id,
                                                      'product_id': product_ids[0],
                                                      'base': -2,
                                                      'margin_per_pax': margin})   
                
                rule_ids = rule.search(cr, uid, [('name', '=', 'Default'),
                                                 ('base', '=', -1), 
                                                ('price_version_id', '=', version_id),
                                                ('base_pricelist_id', '=', pub_pricelist_id)])
                if rule_ids == []:
                     rule.create(cr, uid, {'name': 'Default',
                                           'price_version_id': version_id,
                                           'base': -1,
                                            'base_pricelist_id': pub_pricelist_id})       
                
            
            if msg == '':
                msg += '\n ================== \nMargins successfully uploaded. \n'
            else:
                msg += '\n ================== \nCheck that names are properly typed or present in the system. \n'
            
            msg += 'Press cancel to close'    
                    
            self.write(cr, uid, obj.id, {'result': msg}, context)
            return {
                'name': 'Import Margins',
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'import.margins',
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
