from openerp.models import TransientModel
from openerp import api
import time


class travel_load_data(TransientModel):
    _name = 'travel.load.data'

    @api.model
    def create_car(self, car_name, passagener, transmission, _class, categ_id):
        product_car = self.env['product.car']
        product_car.create({
            'car_name': car_name,
            'name': car_name,
            'passengers': passagener,
            'categ_id': categ_id,
            'transmission_id': transmission,
            'class_id': _class
        })

    @api.model
    def create_flight(self, flight_name, _from, to, categ_id):
        product_car = self.env['product.flight']
        product_car.create({
            'car_name': flight_name,
            'name': flight_name,
            'origin': _from,
            'to': to,
            'categ_id': categ_id
        })

    @api.model
    def create_transfer(self, transfer_name, _from, to, categ_id):
        product_car = self.env['product.transfer']
        product_car.create({
            'car_name': transfer_name,
            'name': transfer_name,
            'origin': _from,
            'to': to,
            'categ_id': categ_id
        })

    @api.model
    def create_supplier_info_and_pricelist(self, table_name, name, supplier_info_name, pricelist):
        product_table_ = self.env['product.' + table_name]
        product = product_table_.search_read([('name', '=', name)])
        if len(product) > 1:
            raise Exception('Several products with same name, something went wrong')
        elif len(product):
            supplier_table = self.env['product.supplierinfo']
            supplier = supplier_table.create({
                'name': supplier_info_name,
                'product_tmpl_id': product[0]['product_tmpl_id'][0]
            })
            pricelist_table = self.env['pricelist.partnerinfo']
            for x in pricelist:
                res = {
                    'price': pricelist[x]['price'],
                    'start_date': time.strftime(pricelist[x]['start_date']),
                    'end_date': time.strftime(pricelist[x]['end_date']),
                    'suppinfo_id': supplier.id
                }
                if table_name.lower() == 'fligth':
                    res.update({'child': pricelist[x]['child']})
                pricelist_table.create(res)
