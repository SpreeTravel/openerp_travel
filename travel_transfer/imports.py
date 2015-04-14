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
            fields.text('Result'),
        'supplier_id':
            fields.many2one('res.partner', 'Supplier'),
        'start_date':
            fields.date('Start date'),
        'end_date':
            fields.date('End date')
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
        data = document.sheet_by_index(sheet)
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

    ''' Transfers '''

    def load_transfer(self, cr, uid, obj, data, context=None):
        product_transfer = self.pool.get('product.transfer')
        product_supplierinfo = self.pool.get('product.supplierinfo')
        pricelist_partnerinfo = self.pool.get('pricelist.partnerinfo')

        dict_options = self.prepare_load(cr, uid, context)
        for d in range(6, data.nrows):
            name = (data.cell_value(d, 0) + ' - ' + data.cell_value(d, 1)).encode('UTF-8')
            transfer_ids = product_transfer.search(cr, uid, [('name', '=', name)], context=context)
            if transfer_ids:
                transfer = product_transfer.browse(cr, uid, transfer_ids[0], context)
            else:
                context.update({'category': 'transfer'})
                transfer_id = product_transfer.create(cr, uid, {'name': name}, context)
                transfer = product_transfer.browse(cr, uid, transfer_id)
            seller_ids = [s.id for s in transfer.seller_ids]
            if seller_ids:
                product_supplierinfo.unlink(cr, uid, seller_ids, context)
            svals = {
                'name': obj.supplier_id.id,
                'product_tmpl_id': transfer.product_id.product_tmpl_id.id,
                'min_qty': 0
            }
            old_suppinfo_id = product_supplierinfo.search(cr, uid, 
                                                          [('name', '=', obj.supplier_id.id),
                                                           ('product_tmpl_id', '=', transfer.product_id.product_tmpl_id.id)])
            product_supplierinfo.unlink(cr, uid, old_suppinfo_id)
            suppinfo_id = product_supplierinfo.create(cr, uid, svals, context)
            for k, v in dict_options.iteritems():
                price = data.cell_value(d, k)
                pvals = {
                    'start_date': obj.start_date,
                    'end_date': obj.end_date,
                    'price': price,
                    'min_quantity': 0,
                    'suppinfo_id': suppinfo_id
                }
                pvals.update(v)
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
