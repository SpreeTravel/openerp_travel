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

from openerp.osv import fields, osv
from openerp.osv.orm import TransientModel
import base64
import datetime
import xlrd

BASE_DATE = 693594

class import_transfer(TransientModel):
    _name = 'import.transfer'
    _columns = {
        'file':
            fields.binary('File'),
        'sheet':
            fields.integer('Sheet'),
        'result':
            fields.text('Result')
    }
    
    _defaults = {'sheet': 0}

    def import_file(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0], context)
        if obj.file:
            origin = base64.decodestring(obj.file)
            try:
                data = self.read_from_calc(origin, obj.sheet)
            except:
                raise osv.except_osv('Error!', 'The file is not valid.')
            self.load_transfer(cr, uid, obj, data, context)
            msg = 'The operation was successful.'
            self.write(cr, uid, obj.id, {'result': msg}, context)
            return {
                'name': 'Import Products',
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'import.transfer',
                'res_id': obj.id,
                'target': 'new',
                'context': context,
            }
        else:
            raise osv.except_osv('Error!', 'You must select a file.')

    def read_from_calc(self, data, sheet, context=None):
        document = xlrd.open_workbook(file_contents=data)
        data = document.sheets()
        return data

    def get_id_by_name(self, cr, uid, model, name, context=None):
        context = context or {}
        obj = self.pool.get(model)
        obj_id = obj.search(cr, uid, [('name', '=', name)], context=context)
        if not obj_id and context.get('create', False):
            vals = {'name': name}
            if context.get('values', False):
                vals.update(context['values'])
            obj_id = [obj.create(cr, uid, vals, context)]
        return obj_id and obj_id[0] or False

    def get_categ_id(self, cr, uid, categ, context=None):
        product = self.pool.get('product.product')
        ctx = context.copy()
        ctx.update({'product_type': categ})
        return product._get_category(cr, uid, ctx)

    def get_value(self, value):
        try:
            return float(value)
        except:
            return False

    def get_date(self, value):
        d = BASE_DATE + int(value)
        return datetime.datetime.fromordinal(d)

    def find_by_code(self, cr, uid, code, model, context=None):
        obj = self.pool.get(model)
        val = obj.search(cr, uid, [('code', '=', code)], context=context)[0]
        return val  
       
    def find_by_name(self, cr, uid, name, model, context=None):
        obj = self.pool.get(model)
        val = obj.search(cr, uid, [('name', '=', code)], context=context)[0]
        return val 
    
    def get_option_value(self, cr, uid, name, code, context=None):
        ot = self.pool.get('option.type')
        ov = self.pool.get('option.value')

        ot_id = ot.search(cr, uid, [('code', '=', code)], context=context)[0]
        to_search = [('name', '=', name), ('option_type_id', '=', ot_id)]
        ov_ids = ov.search(cr, uid, to_search, context=context)
        if ov_ids:
            return ov_ids[0]
        else:
            raise Exception()
    
    ''' Transfers '''

    def load_transfer(self, cr, uid, obj, data, context=None):
        product_transfer = self.pool.get('product.transfer')
        product_supplierinfo = self.pool.get('product.supplierinfo')
        pricelist_partnerinfo = self.pool.get('pricelist.partnerinfo')
        partner = self.pool.get('res.partner')
        transfer_categ_id = self.pool.get('product.category').search(cr, uid, [('name', '=', 'Transfer')])[0]
        
        msg = ''
        sheet = data[-1]
        
        head = {sheet.cell_value(1, x): x for x in range(sheet.ncols)} 
        
        date_from = sheet.cell_value(0, 0)
        date_to   = sheet.cell_value(0, 1)
    
        for r in range(2, sheet.nrows):
            
            def cell(attr):
                if sheet.cell(r, head[attr]).ctype == xlrd.XL_CELL_ERROR:
                    return None
                return sheet.cell_value(r, head[attr])
            
            suppinfo_id = False
            transfer_obj = False
            min_paxs = False
            max_paxs = False
            vehicle_type_id = False
            guide_id = False
            confort_id = False
            price = False
            
            if cell('Name'):                                
                transfer_name = cell('Name').strip()
                transfer_ids = product_transfer.search(cr, uid, [('name', '=', transfer_name)])
                if len(transfer_ids) == 0:
                    transfer_id = product_transfer.create(cr, uid, {'name': transfer_name, 'categ_id': transfer_categ_id}, context)
                    transfer_obj = product_transfer.browse(cr, uid, transfer_id)
                elif len(transfer_ids) > 1: 
                    msg += 'Ambiguous name for transfer: '+ transfer_name + '\n'
                    continue
                else:
                    transfer_obj = product_transfer.browse(cr, uid, transfer_ids[0], context)
                
            if cell('Supplier'):
                if transfer_obj:
                   suppinfo_id = None
                   supplier_name = str(cell('Supplier')).strip()
                   if supplier_name != '':
                       partner_ids = partner.search(cr, uid, [('name', '=', supplier_name)])
                       if len(partner_ids) == 0:
                           msg += 'Supplier name not found: '+ supplier_name + '\n'
                           continue
                       elif len(partner_ids) > 1: 
                           msg += 'Ambiguous name for supplier: '+ supplier_name + '\n'
                           continue
                       else:
                           partner_id = partner_ids[0]
                           suppinfo_ids = product_supplierinfo.search(cr, uid, ['&', 
                                                                                ('name', '=', partner_id), 
                                                                                ('product_tmpl_id', '=', transfer_obj.product_tmpl_id.id)], 
                                                                      context=context)
                           if len(suppinfo_ids) == 0:        
                               svals = {
                                   'name': partner_id,
                                   'product_tmpl_id': transfer_obj.product_tmpl_id.id,
                                   'min_qty': 0
                               }
                               suppinfo_id = product_supplierinfo.create(cr, uid, svals, context)
                           else:
                               suppinfo_id = suppinfo_ids[0] 
                               
            if cell('Min paxs'):
                try: 
                    min_paxs = int(cell('Min paxs'))
                except:
                    msg += 'Wrong min paxs for: '+ transfer_name + '\n'
                    continue
            if cell('Max paxs'):
                try:
                    max_paxs = int(cell('Max paxs'))
                except:
                    msg += 'Wrong max paxs for: '+ transfer_name + '\n'
                    continue
            if cell('Vehicle type'):
                try:
                    vehicle_type_id = self.get_option_value(cr, uid, cell('Vehicle type'), 'vt', context).upper()
                except:
                    msg += 'Wrong vehicle type option in '+ transfer_name + '\n'
                    continue
            if cell('Guide'):
                try:
                    guide_id = self.get_option_value(cr, uid, cell('Guide'), 'guide', context).upper()
                except:
                    msg += 'Wrong guide option in '+ transfer_name + '\n'
                    continue
            if cell('Confort'):
                try:
                    confort = self.get_option_value(cr, uid, cell('Confort'), 'vc', context).upper()
                except:
                    msg += 'Wrong confort option in '+ transfer_name + '\n'
                    continue
            if cell('Price'):
                try:
                    price = float(cell('Price'))
                except:
                    msg += 'Wrong price for: '+ transfer_name + '\n'
                    continue

            if suppinfo_id and transfer_obj and min_paxs and max_paxs and vehicle_type and guide and confort and price:
                pvals = {'start_date': date_from,
                         'end_date': date_to,
                         'price': price,
                         'min_quantity': 0,
                         'suppinfo_id': suppinfo_id,
                         'min_paxs': min_paxs,
                         'max_paxs': max_paxs,
                         'vehicle_type_id': vehicle_type,
                         'guide_id': guide,
                         'confort_id': confort_id
                         }
            pricelist_partnerinfo.create(cr, uid, pvals, context)
        return True

    def prepare_load(self, cr, uid, context):
        model = 'option.value'
        taxi = self.find_by_code(cr, uid, 'taxi', model, context)
        microbus = self.find_by_code(cr, uid, 'micro', model, context)
        minibus = self.find_by_code(cr, uid, 'mini', model, context)
        omnibus = self.find_by_code(cr, uid, 'omni', model, context)
        guide = self.find_by_code(cr, uid, 'guide', model, context)
        no_guide = self.find_by_code(cr, uid, 'no_guide', model, context)
        confort_s = self.find_by_code(cr, uid, 'vcs', model, context)
        confort_l = self.find_by_code(cr, uid, 'vcl', model, context)

        dict_options = {
            2:  {'vehicle_type_id': taxi,     'guide_id': no_guide, 'min_paxs': 1,  'max_paxs': 2,  'confort_id': confort_s},
            3:  {'vehicle_type_id': taxi,     'guide_id': guide,    'min_paxs': 1,  'max_paxs': 2,  'confort_id': confort_s},
            4:  {'vehicle_type_id': taxi,     'guide_id': no_guide, 'min_paxs': 1,  'max_paxs': 2,  'confort_id': confort_l},
            5:  {'vehicle_type_id': taxi,     'guide_id': guide,    'min_paxs': 1,  'max_paxs': 2,  'confort_id': confort_l},
            6:  {'vehicle_type_id': microbus, 'guide_id': no_guide, 'min_paxs': 3,  'max_paxs': 5,  'confort_id': confort_s},
            7:  {'vehicle_type_id': microbus, 'guide_id': no_guide, 'min_paxs': 6,  'max_paxs': 8,  'confort_id': confort_s},
            8:  {'vehicle_type_id': microbus, 'guide_id': guide,    'min_paxs': 3,  'max_paxs': 5,  'confort_id': confort_s},
            9:  {'vehicle_type_id': microbus, 'guide_id': guide,    'min_paxs': 6,  'max_paxs': 8,  'confort_id': confort_s},
            10: {'vehicle_type_id': minibus,  'guide_id': guide,    'min_paxs': 9,  'max_paxs': 12, 'confort_id': confort_s},
            11: {'vehicle_type_id': minibus,  'guide_id': guide,    'min_paxs': 13, 'max_paxs': 20, 'confort_id': confort_s},
            12: {'vehicle_type_id': omnibus,  'guide_id': guide,    'min_paxs': 21, 'max_paxs': 30, 'confort_id': confort_s},
            13: {'vehicle_type_id': omnibus,  'guide_id': guide,    'min_paxs': 31, 'max_paxs': 43, 'confort_id': confort_s}
        }
        return dict_options
