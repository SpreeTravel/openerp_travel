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

import xlrd
from openerp.exceptions import except_orm
from openerp import api, fields
from openerp.models import TransientModel
from openerp.tools.translate import _


class import_car(TransientModel):
    _inherit = 'import.modules'

    car_excels = fields.Binary(_('Car\'s Excels'))

    @api.model
    def import_car(self, document):
        car = self.env['product.car']
        msg = {
            'created': 0,
            'updated': 0,
        }
        pp = self.env['product.product']
        pt = self.env['product.template']
        pc = self.env['product.category']
        supplier = self.env['res.partner']
        supplierinfo = self.env['product.supplierinfo']
        supplement = self.env['product.rate.supplement']
        partnerinfo = self.env['pricelist.partnerinfo']
        for sheet in document.sheets():
            head = {sheet.cell_value(0, x).encode('latin1'): x for x in range(sheet.ncols)}
            for r in range(1, sheet.nrows):
                def cell(attr):
                    try:
                        if sheet.cell(r, head[attr]).ctype == xlrd.XL_CELL_ERROR:
                            return None
                        return sheet.cell_value(r, head[attr])
                    except KeyError:
                        raise except_orm('Error', _('Wrong header: ') + str(attr))

                if sheet.name.lower() == 'carros':
                    name_d = False
                    if cell('Nombre'):
                        name = cell('Nombre').upper()
                        car_obj = car.search([('car_name', '=', name)])
                        if car_obj.id:
                            msg['updated'] += 1
                        else:
                            name_d = True
                    if cell('Clase'):
                        clase_name = cell('Clase').upper()
                        clase = self.get_option_value(clase_name, 'cl')
                    if cell('Transmisión'):
                        tr_name = cell('Transmisión').upper()
                        tr = self.get_option_value(tr_name, 'tm')
                    if name_d:
                        msg['created'] += 1
                        cat = pc.search([('name', '=', 'Car')])
                        pt_temp = pt.create({
                            'name': name,
                            'categ_id': cat.id,
                        })
                        pp_temp = pp.create({
                            'product_tmpl_id': pt_temp.id,
                            'name_template': name
                        })
                        car.create({
                            'car_name': name,
                            'product_id': pp_temp.id,
                            'passengers': cell('Pasajeros'),
                            'class_id': clase.id or False,
                            'transmission_id': tr.id or False
                        })
                    else:
                        car_obj.write({
                            'passengers': cell('Pasajeros'),
                            'class_id': clase.id or False,
                            'transmission_id': tr.id or False
                        })

                elif sheet.name.lower() == 'proveedores':
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

                elif sheet.name.lower() == 'precios':
                    car_obj = None
                    supp_obj = None
                    start_date = False
                    end_date = False
                    price = 0.0
                    if cell('Carro'):
                        name = cell('Carro').upper()
                        car_obj = car.search([('car_name', '=', name)])
                        if not car_obj.id:
                            raise except_orm('Error', _('Car: ') + str(name) + _(' not found!!!!!!') + '\n')
                    if cell('Proveedor'):
                        supp_obj = self.get_supplier(cell('Proveedor').upper(), supplier)
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
                    partnerinfo.create({
                        'suppinfo_id': supplierinfo_tmp.id,
                        'start_date': start_date,
                        'end_date': end_date,
                        'price': price
                    })
                    msg['created'] += 1

                elif sheet.name.lower() == 'suplementos':
                    car_obj = None
                    supp_obj = None
                    start_date = False
                    end_date = False
                    price = 0.0
                    if cell('Carro'):
                        name = cell('Carro').upper()
                        car_obj = car.search([('car_name', '=', name)])
                        if not car_obj.id:
                            raise except_orm('Error', _('Car: ') + str(name) + _(' not found!!!!!!') + '\n')
                    if cell('Proveedor'):
                        supp_obj = self.get_supplier(cell('Proveedor').upper(), supplier)
                    if cell('Nombre suplemento'):
                        sup = cell('Nombre suplemento')
                        sup_obj = self.get_option_value(sup, 'sup')
                        if not sup_obj:
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

                else:
                    raise except_orm('Error', _('Wrong excel information!!!'))

        return msg
