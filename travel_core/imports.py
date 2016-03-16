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
from openerp.exceptions import except_orm
from openerp import fields, api
from openerp.models import TransientModel
from openerp.tools.translate import _

BASE_DATE = 693594

modules = [('car', 'Cars')]


class import_modules(TransientModel):
    _name = 'import.modules'
    file = fields.Binary(_('File'))
    choices = fields.Selection(modules, _('Selection'))
    result = fields.Text(_('Result'))

    @api.multi
    def execute_import(self):
        obj = self[0]
        if obj.file:
            data = base64.decodestring(obj.file)
            document = xlrd.open_workbook(file_contents=data, encoding_override='cp1252')
            msg = getattr(obj, 'import_' + obj.choices)(document)
            self.write(obj.id, {'result': msg})
            return {
                'name': 'Import Excels',
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'import.modules',
                'res_id': obj.id,
                'target': 'new',
                'context': {},
            }
        else:
            raise except_orm(_('Error!'), _('You must select a file.'))

    def get_date(self, value):
        try:
            d = BASE_DATE + int(value)
            return datetime.datetime.fromordinal(d)
        except:
            return datetime.datetime(1901, 1, 1)

    def get_float(self, value):
        try:
            return float(value)
        except:
            return 0.0

    @api.model
    def get_option_value(self, name, code):
        ot = self.env['option.type']
        ov = self.env['option.value']

        ot_id = ot.search([('code', '=', code)])
        to_search = [('name', '=', name), ('option_type_id', '=', ot_id.id)]
        ov_ids = ov.search(to_search)
        return ov_ids
