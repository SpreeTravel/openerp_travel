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


class import_package(TransientModel):
    _inherit = 'import.modules'

    package_excels = fields.Binary(_('Package\'s Excels'))

    @api.model
    def import_package(self, document):
        package = self.env['product.package']
        package_lines = self.env['product.package.line']
        category = self.env['product.category']
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
                        raise except_orm('Error', _('Header: ') + unicode(attr) + _(' not exist!!'))

                if sheet.name.lower() == 'paquetes':
                    name_d = False
                    if cell('Nombre'):
                        name = cell('Nombre').upper()
                        package_obj = package.search([('package_name', '=', name)])
                        if package_obj.id:
                            msg['updated'] += 1
                        else:
                            name_d = True

                    if cell('Días'):
                        days = self.get_int(cell('Días'))
                    if cell('Categoría'):
                        categ = cell('Categoría')
                        categ_obj = category.search([('name', '=', categ)])
                        if not categ_obj.id:
                            raise except_orm('Error', _('Category: ') + categ + ' not exist!!!!!!')
                    if cell('Producto'):
                        product = cell('Producto').upper()
                        product_obj = pp.search([('name_template', '=', product)])
                        if not product_obj.id:
                            raise except_orm('Error', _('Product: ') + product + ' not exist!!!!!!')
                    if cell('Proveedor'):
                        supl = cell('Proveedor').upper()
                        supl_obj = supplier.search([('name', '=', supl)])
                        if not supl_obj.id:
                            supl_obj = supplier.create({
                                'name': supl
                            })
                    if name_d:
                        msg['created'] += 1
                        cat = pc.search([('name', '=', 'Package')])
                        pt_temp = pt.create({
                            'name': name,
                            'categ_id': cat.id,
                        })
                        pp_temp = pp.create({
                            'product_tmpl_id': pt_temp.id,
                            'name_template': name
                        })
                        package_obj = package.create({
                            'package_name': name,
                            'product_id': pp_temp.id,

                        })
                    lines = package_lines.search([('package_id', '=', package_obj.id)])
                    if len(lines):
                        order = max(lines, key=lambda x: x.order).order + 1
                    else:
                        order = 1
                    package_lines.create({
                        'package_id': package_obj.id,
                        'order': order,
                        'num_day': days,
                        'supplier_id': supl_obj.id,
                        'product_id': product_obj.id,
                        'category_id': categ_obj.id
                    })

                elif sheet.name.lower() == 'proveedores':
                    msg = self.set_supplier(cell, supplier, msg)

                elif sheet.name.lower() == 'precios':
                    package_obj = None
                    supp_obj = None
                    start_date = False
                    end_date = False
                    price = 0.0
                    if cell('Paquete'):
                        name = cell('Paquete').upper()
                        package_obj = package.search([('package_name', '=', name)])
                        if not package_obj.id:
                            raise except_orm('Error', _('package: ') + str(name) + _(' not found!!!!!!') + '\n')
                    if cell('Proveedor'):
                        supp_obj = self.get_supplier(cell('Proveedor').upper(), supplier)
                    if cell('Fecha inicio'):
                        start_date = self.get_date(cell('Fecha inicio'))
                    if cell('Fecha fin'):
                        end_date = self.get_date(cell('Fecha fin'))
                    if cell('Precio'):
                        price = self.get_float(cell('Precio'))
                    if cell('Mínimo pasajeros'):
                        min_pax = self.get_int(cell('Mínimo pasajeros'))
                    if cell('Máximo pasajeros'):
                        max_pax = self.get_int(cell('Máximo pasajeros'))
                    supplierinfo_tmp = supplierinfo.search(
                        [('name', '=', supp_obj.id),
                         ('product_tmpl_id', '=', package_obj.product_id.product_tmpl_id.id)])
                    if not supplierinfo_tmp.id:
                        supplierinfo_tmp = supplierinfo.create({
                            'name': supp_obj.id,
                            'product_tmpl_id': package_obj.product_id.product_tmpl_id.id
                        })
                    partnerinfo.create({
                        'suppinfo_id': supplierinfo_tmp.id,
                        'start_date': start_date,
                        'end_date': end_date,
                        'price': price,
                        'min_paxs': min_pax,
                        'max_paxs': max_pax
                    })
                    msg['created'] += 1

                elif sheet.name.lower() == 'suplementos':
                    msg = self.set_supplement('Paquete', 'package', cell, supplement, package, supplier,
                                              supplierinfo, msg)

                else:
                    raise except_orm('Error', _('Wrong excel information!!!'))

        return msg
