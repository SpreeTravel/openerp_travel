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


class import_car(TransientModel):
    _inherit = 'import.modules'

    @api.model
    def import_car(self, document):
        car = self.env['product.car']
        msg = ''
        pp = self.env['product.product']
        pt = self.env['product.template']
        supplier = self.env['res.partner']
        supplierinfo = self.env['product.supplierinfo']
        supplement = self.env['product.rate.supplement']
        partnerinfo = self.env['pricelist.partnerinfo']
        for sheet in document.sheets():
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

                if sheet.name.lower() == 'carros':
                    if cell('Nombre'):
                        name = cell('Nombre').upper()
                        car_obj = car.search([('car_name', '=', name)])
                        if len(car_obj) >= 1:
                            msg += _('Ambiguous Car: ') + name + '\n'
                            name_d = False
                        else:
                            name_d = True
                    if cell('Clase'):
                        clase_name = cell('Clase').upper()
                        clase = self.get_option_value(clase_name, 'cl')
                    if cell('Transmisión'):
                        tr_name = cell('Transmisión').upper()
                        tr = self.get_option_value(tr_name, 'tm')
                    if name_d:
                        car.create({
                            'car_name': name,
                            'passengers': cell('Pasajeros'),
                            'class_id': clase.id or False,
                            'transmission_id': tr.id or False
                        })

                if sheet.name.lower() == 'proveedor':
                    company_obj = None
                    if cell('Nombre'):
                        name = cell('Nombre').upper()
                        sup_obj = supplier.search([('name', '=', name)])
                        if sup_obj:
                            msg += _('Ambiguous Supplier: ') + name + '\n'
                            name_d = False
                        else:
                            name_d = True
                    if cell('Compañía'):
                        company = cell('Compañía').upper()
                        company_obj = supplier.search([('name', '=', company)])
                        if company_obj:
                            company_obj = company_obj.id
                    if name_d:
                        supplier.create({
                            'name': name,
                            'company_id': company_obj,
                            'street': cell('Dirección'),
                            'website': cell('Sitio web'),
                            'phone': cell('Teléfono'),
                            'email': cell('Email'),
                            'fax': cell('Fax')
                        })

                if sheet.name.lower() == 'precios':
                    car_obj = None
                    supp_obj = None
                    start_date = False
                    end_date = False
                    price = 0.0
                    if cell('Carro'):
                        name = cell('Carro').upper()
                        car_obj = car.search([('car_name', '=', name)])
                        if not car_obj:
                            msg += _('Car: ') + str(name) + _(' not found!!!!!!')
                    if cell('Proveedor'):
                        supplier = cell('Proveedor').upper()
                        supp_obj = supplier.search([('name', '=', supplier)])
                        if not supp_obj:
                            msg += _('Supplier: ') + str(supplier) + _(' not found!!!!!!')
                    if cell('Fecha inicio'):
                        start_date = self.get_date(cell('Fecha inicio'))
                    if cell('Fecha fin'):
                        end_date = self.get_date(cell('Fecha fin'))
                    if cell('Precio'):
                        price = self.get_float(cell('Precio'))
                    if car_obj and supp_obj:
                        supplierinfo_tmp = supplierinfo.search(
                            [('name', '=', supp_obj.id), ('product_tmpl_id', '=', car_obj.product_id.product_tmpl_id)])
                        if not supplierinfo_tmp:
                            supplierinfo_tmp = supplierinfo.create({
                                'name': supp_obj.id,
                                'product_tmpl_id': car_obj.product_id.product_tmpl_id
                            })
                        partnerinfo.create({
                            'suppinfo_id': supplierinfo_tmp.id,
                            'start_date': start_date,
                            'end_date': end_date,
                            'price': price
                        })

                    create = False

                if sheet.name.lower() == 'suplementos':
                    car_obj = None
                    supp_obj = None
                    start_date = False
                    end_date = False
                    price = 0.0
                    if cell('Carro'):
                        name = cell('Carro').upper()
                        car_obj = car.search([('car_name', '=', name)])
                        if not car_obj:
                            msg += _('Car: ') + str(name) + _(' not found!!!!!!')
                    if cell('Proveedor'):
                        supplier = cell('Proveedor').upper()
                        supp_obj = supplier.search([('name', '=', supplier)])
                        if not supp_obj:
                            msg += _('Supplier: ') + str(supplier) + _(' not found!!!!!!')
                    if cell('Nombre suplemento'):
                        sup = cell('Nombre suplemento').upper()
                        sup_obj = self.get_option_value(sup, 'sup')
                        if not sup_obj:
                            msg += _('Supplement: ') + str(sup) + _(' not found!!!!!!')
                    if cell('Fecha inicio'):
                        start_date = self.get_date(cell('Fecha inicio'))
                    if cell('Fecha fin'):
                        end_date = self.get_date(cell('Fecha fin'))
                    if cell('Precio'):
                        price = self.get_float(cell('Precio'))
                    if car_obj and supp_obj and sup_obj:
                        supplierinfo_tmp = supplierinfo.search(
                            [('name', '=', supp_obj.id), ('product_tmpl_id', '=', car_obj.product_id.product_tmpl_id)])
                        if not supplierinfo_tmp:
                            supplierinfo_tmp = supplierinfo.create({
                                'name': supp_obj.id,
                                'product_tmpl_id': car_obj.product_id.product_tmpl_id
                            })
                        supplement.create({
                            'suppinf_id': supplierinfo_tmp.id,
                            'start_date': start_date,
                            'end_date': end_date,
                            'price': price,
                            'supplement_id': sup_obj.id
                        })
        if msg == '':
            msg += _('\n ================== \nRental information successfully uploaded. \n')
        else:
            msg += _('\n ================== \nCheck that names are properly typed or present in the system. \n')
        msg += _('Press cancel to close')
        return msg
