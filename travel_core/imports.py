# -*- coding: latin1 -*-
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

modules = [('car', _('Cars')),
           ('flight', _('Flights')),
           ('hotel', _('Hotels')),
           ('transfer', _('Transfers')),
           ('package', _('Packages'))]


class import_modules(TransientModel):
    _name = 'import.modules'
    file = fields.Binary(_('File'))
    choices = fields.Selection(modules, _('Selection'))
    result = fields.Text(_('Result'))

    @api.multi
    def execute_import(self):
        obj = self[0]
        if not obj.choices:
            raise except_orm('Error', 'You have to select a category!!!')
        if obj.file:
            data = base64.decodestring(obj.file)
            try:
                document = xlrd.open_workbook(file_contents=data)
            except:
                raise except_orm('Error', _('Wrong file!!!'))
            msg = getattr(obj, 'import_' + obj.choices)(document)
            msg = str(msg) + '\n'
            msg += _('Press cancel to close')
            if msg:
                obj.write({'result': msg})
            else:
                obj.write({'result': _('Import successfully!!!!')})
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

    @api.model
    def get_date(self, value):
        try:
            d = BASE_DATE + int(value)
            return datetime.datetime.fromordinal(d)
        except:
            return datetime.datetime(1901, 1, 1)

    @api.model
    def get_float(self, value):
        try:
            return float(value)
        except:
            return 0.0

    @api.model
    def get_int(self, value):
        try:
            return int(value)
        except:
            return 0

    @api.model
    def get_supplier(self, value, supplier):
        supp_obj = supplier.search([('name', '=', value)])
        if not supp_obj.id:
            raise except_orm('Error', _('Supplier: ') + str(value) + _(' not found!!!!!!') + '\n')
        return supp_obj

    @api.model
    def get_option_value(self, name, code):
        name = name.upper()
        ot = self.env['option.type']
        ov = self.env['option.value']

        ot_id = ot.search([('code', '=', code)])
        if not ot_id.id:
            raise except_orm('Error', _('Code:') + str(code) + _(' not exist!!!!'))
        to_search = [('name', '=', name), ('option_type_id', '=', ot_id.id)]
        ov_ids = ov.search(to_search)
        if not ov_ids.id:
            code = name
            if len(name) > 3:
                code = name[:3]
            ov_ids = ov.create({
                'name': name,
                'code': code,
                'option_type_id': ot_id.id
            })
        return ov_ids

    @api.model
    def set_supplier(self, cell, supplier, msg):
        company_obj = None
        if cell('Nombre'):
            name = cell('Nombre').upper()
            sup_obj = supplier.search([('name', '=', name)])
            if sup_obj.id:
                msg['updated'] += 1
                name_d = False
            else:
                name_d = True
        if cell('Compañía'):
            company = cell('Compañía').upper()
            company_obj = supplier.search([('name', '=', company)])
            if company_obj.id:
                company_obj = company_obj.id
            else:
                raise except_orm('Error', _('Company Name: ') + name + _('not found!!!!!!!!!'))

        if name_d:
            msg['created'] += 1
            supplier.create({
                'name': name,
                'company_id': company_obj,
                'street': cell('Dirección'),
                'website': cell('Sitio web'),
                'phone': cell('Teléfono'),
                'email': cell('Email'),
                'fax': cell('Fax')
            })
        else:
            supplier.write({
                'street': cell('Dirección'),
                'website': cell('Sitio web'),
                'phone': cell('Teléfono'),
                'email': cell('Email'),
                'fax': cell('Fax')
            })
        return msg

    @api.model
    def set_supplement(self, field, _type, cell, supplement, car, supplier, supplierinfo, msg):
        car_obj = None
        supp_obj = None
        start_date = False
        end_date = False
        price = 0.0
        if cell(field):
            name = cell(field).upper()
            car_obj = car.search([(_type + '_name', '=', name)])
            if not car_obj.id:
                raise except_orm('Error', _(_type.capitalize() + ': ') + str(name) + _(' not found!!!!!!') + '\n')
        if cell('Proveedor'):
            supp_obj = self.get_supplier(cell('Proveedor').upper(), supplier)
        if cell('Nombre suplemento'):
            sup = cell('Nombre suplemento')
            sup_obj = self.get_option_value(sup, 'sup')
            if not sup_obj.id:
                if cell('Código suplemento'):
                    ov = self.env['option.value']
                    ot = self.env['option.type']
                    sup_tmp = ot.search([('code', '=', 'sup')])
                    ov.create({
                        'code': cell('Código suplemento'),
                        'name': cell('Nombre suplemento'),
                        'option_type_id': sup_tmp.id
                    })
                else:
                    except_orm('Error', _('Suplement: ') + sup + ' don\'t have code' + '\n')
        if cell('Fecha inicio'):
            start_date = self.get_date(cell('Fecha inicio'))
        if cell('Fecha fin'):
            end_date = self.get_date(cell('Fecha fin'))
        if cell('Precio'):
            price = self.get_float(cell('Precio'))
        supplierinfo_tmp = supplierinfo.search(
            [('name', '=', supp_obj.id), ('product_tmpl_id', '=', car_obj.product_id.product_tmpl_id.id)])
        if not supplierinfo_tmp.id:
            supplierinfo_tmp = supplierinfo.create({
                'name': supp_obj.id,
                'product_tmpl_id': car_obj.product_id.product_tmpl_id.id
            })
        supplement.create({
            'suppinfo_id': supplierinfo_tmp.id,
            'start_date': start_date,
            'end_date': end_date,
            'price': price,
            'supplement_id': sup_obj.id
        })
        msg['created'] += 1
        return msg
