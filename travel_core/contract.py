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

from openerp.osv import fields
from openerp.osv.orm import Model


# TODO: ver por fin si vale la pena hacerle una vista a esta clase
class supplier_contract(Model):
    _name = 'supplier.contract'
    _inherit = 'supplier.contract'
    _columns = {
        'supplier_id': fields.many2one('res.partner', 'Supplier',
                                       domain="[('supplier', '=', True)]"),
        'start_date': fields.date('Start Date'),
        'end_date': fields.date('End Date')
    }
