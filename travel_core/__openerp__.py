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

{
    "name": "Travel Agency - Core",
    "version": "0.1",
    "author": "OpenJAF.",
    "website": "http://www.openjaf.com",
    "category": "Sales",
    "description": """

Base module for managing sales, prices and accounting in a Travel Agency
========================================================================

    """,
    "depends": ['sale', 'contacts'],
    "init_xml": [
        'data/options.xml',
        'data/pricelist.xml',
        'data/menu.xml'
    ],
    "data": ['view/report_saleorder.xml',
             'report/hotels_report_view.xml',
             'report/flights_report_view.xml',
             'report/transfer_report_view.xml',
             'report/car_report_view.xml'],
    "update_xml": [
        'view/base.xml',
        'view/pricelist.xml',
        'view/sale.xml',
        'report/sale_report_view.xml',
        'report/default_voucher.xml',
        'report/travel_voucher.xml',
        'security/ir.model.access.csv'
    ],
    "demo_xml": [],
    "application": False,
    "installable": True,
}
