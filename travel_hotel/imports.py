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


class import_hotel(TransientModel):
    _inherit = 'import.modules'

    def _get_excel(self):
        return 'https://www.googledrive.com/host/0B3qOsAnXwRFhN251MUlmUlNjVWs/Hoteles.xlsx'

    hotel_excels = fields.Char(_('Hotel\'s Excels'), default=_get_excel)

    @api.model
    def import_hotel(self, document):
        hotel = self.env['product.hotel']
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

                if sheet.name.lower() == 'hoteles':
                    dtn = self.env['destination']
                    name_d = False
                    if cell('Nombre'):
                        name = cell('Nombre').upper()
                        hotel_obj = hotel.search([('hotel_name', '=', name)])
                        if hotel_obj.id:
                            msg['updated'] += 1
                        else:
                            name_d = True
                    if cell('Destinos'):
                        origen = cell('Destinos').upper()
                        org_obj = dtn.search([('name', '=', origen)])
                        if not org_obj.id:
                            org_obj = dtn.create({
                                'name': origen
                            })
                    if cell('Estrellas'):
                        stars = self.get_int(cell('Estrellas'))
                    if cell('Cadena Hotelera'):
                        chain = cell('Cadena Hotelera').upper()
                        chain_obj = supplier.search([('name', '=', chain)])
                        if not chain_obj.id:
                            chain_obj = supplier.create({
                                'name': chain
                            })
                    if cell('Contacto'):
                        contact = cell('Contacto').upper()
                        cont_obj = supplier.search([('name', '=', contact)])
                        if not cont_obj.id:
                            cont_obj = supplier.create({
                                'name': contact
                            })
                    if name_d:
                        msg['created'] += 1
                        cat = pc.search([('name', '=', 'Hotel')])
                        pt_temp = pt.create({
                            'name': name,
                            'categ_id': cat.id,
                        })
                        pp_temp = pp.create({
                            'product_tmpl_id': pt_temp.id,
                            'name_template': name
                        })
                        hotel.create({
                            'hotel_name': name,
                            'product_id': pp_temp.id,
                            'stars': str(stars),
                            'chain_id': chain_obj.id,
                            'res_partner_id': cont_obj.id,
                            'destination': org_obj.id
                        })
                    else:
                        hotel_obj.write({
                            'stars': str(stars),
                            'chain_id': chain_obj.id,
                            'res_partner_id': cont_obj.id,
                            'destination': org_obj.id
                        })

                elif sheet.name.lower() == 'proveedores':
                    msg = self.set_supplier(cell, supplier, msg)

                elif sheet.name.lower() == 'precios':
                    hotel_obj = None
                    supp_obj = None
                    start_date = False
                    end_date = False
                    price = 0.0
                    if cell('Hotel'):
                        name = cell('Hotel').upper()
                        hotel_obj = hotel.search([('hotel_name', '=', name)])
                        if not hotel_obj.id:
                            raise except_orm('Error', _('hotel: ') + str(name) + _(' not found!!!!!!') + '\n')
                    if cell('Proveedor'):
                        supp_obj = self.get_supplier(cell('Proveedor').upper(), supplier)
                    if cell('Fecha inicio'):
                        start_date = self.get_date(cell('Fecha inicio'))
                    if cell('Fecha fin'):
                        end_date = self.get_date(cell('Fecha fin'))
                    if cell('Habitación'):
                        room = self.get_option_value(cell('Habitación'), 'rt')
                    if cell('Plan'):
                        plan = self.get_option_value(cell('Plan'), 'mp')
                    if cell('Simple'):
                        simple = self.get_float(cell('Simple'))
                    if cell('Doble'):
                        double = self.get_float(cell('Doble'))
                    if cell('Triple'):
                        triple = self.get_float(cell('Triple'))
                    if cell('Adulto Extra'):
                        extra_adult = self.get_float(cell('Adulto Extra'))
                    if cell('Niño'):
                        child = self.get_float(cell('Niño'))
                    if cell('Segundo niño'):
                        extra_child = self.get_float(cell('Segundo niño'))

                    supplierinfo_tmp = supplierinfo.search(
                        [('name', '=', supp_obj.id),
                         ('product_tmpl_id', '=', hotel_obj.product_id.product_tmpl_id.id)])
                    if not supplierinfo_tmp.id:
                        supplierinfo_tmp = supplierinfo.create({
                            'name': supp_obj.id,
                            'product_tmpl_id': hotel_obj.product_id.product_tmpl_id.id
                        })
                    partnerinfo.create({
                        'suppinfo_id': supplierinfo_tmp.id,
                        'start_date': start_date,
                        'end_date': end_date,
                        'room_type_id': room.id,
                        'meal_plan_id': plan.id,
                        'simple': simple,
                        'price': double,
                        'triple': triple,
                        'extra_adult': extra_adult,
                        'child': child,
                        'second_child': extra_child,
                    })
                    msg['created'] += 1

                elif sheet.name.lower() == 'suplementos':
                    msg = self.set_supplement('Hotel', 'hotel', cell, supplement, hotel, supplier, supplierinfo, msg)

                else:
                    raise except_orm('Error', _('Wrong excel information!!!'))

        return msg
