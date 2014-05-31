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


class travel_data(TransientModel):
    _name = 'travel.data'
    _columns = {
        'category_id':
            fields.many2one('product.category', 'Category',
                            domain="[('type', '=', 'normal')]"),
        'file':
            fields.binary('File'),
        'sheet':
            fields.integer('Sheet'),
        'result':
            fields.text('Result')
    }

    def import_file(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0], context)
        if obj.file:
            origin = base64.decodestring(obj.file)
            try:
                data = self.read_from_calc(origin, obj.sheet)
            except:
                raise osv.except_osv('Error!', 'The file is not valid.')
            method = 'load_' + obj.category_id.name.lower()
            res = getattr(self, method)(cr, uid, data, context)
            if res:
                msg = 'Products not found: \n'
                msg += str(res).replace(',', '\n')
            else:
                msg = 'The operation was successful.'
            self.write(cr, uid, obj.id, {'result': msg}, context)
            return {
                'name': 'Import Products',
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'travel.data',
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

    def find_by_name(self, cr, uid, model, name, create, context=None):
        context = context or {}
        obj = self.pool.get(model)
        obj_id = obj.search(cr, uid, [('name', '=', name)], context=context)
        if not obj_id and create:
            vals = {'name': name}
            if context.get('values', False):
                vals.update(context['values'])
            obj_id = [obj.create(cr, uid, vals, context)]
        return obj_id and obj_id[0] or False

    def find_by_code(self, cr, uid, code, model, context=None):
        obj = self.pool.get(model)
        val = obj.search(cr, uid, [('code', '=', code)], context=context)[0]
        return val

    def get_value(self, value):
        try:
            return float(value)
        except:
            return False

    def get_date(self, value):
        d = BASE_DATE + int(value)
        return datetime.datetime.fromordinal(d)
