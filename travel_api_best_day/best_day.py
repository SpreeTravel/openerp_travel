import requests
from lxml import etree

from openerp import models, fields
from openerp.tools.translate import _
from openerp.exceptions import except_orm
import time


class destination(models.Model):
    _inherit = 'destination'

    best_day_id = fields.Char(_('Best Day ID'))


class api_best_day(models.TransientModel):
    _name = 'api.best.day'
    url = fields.Char(_('Url'))
    username = fields.Char(_('Username'))
    password = fields.Char(_('Password'))

    def fill_credentials(self):
        return {
            'a': self.username,
            'ip': self.password
        }

    def get_all_hotels(self, dest):
        url = 'http://testxml.e-tsw.com/AffiliateService/AffiliateService.svc/restful/GetHotelsComplete'
        params = self.fill_credentials()
        params['d'] = dest.best_day_id
        r = self.send_request(url, params)
        hotels = self.env['product.hotel']
        ps = self.env['product.supplierinfo']
        rp = self.env['res.partner']
        text = self.encode(r)
        hotels = etree.fromstring(text)
        for hotel in hotels:
            name = hotel[1].text
            h = hotels.search(['hotel_name', '=', name])
            if not (h and h.id):
                hotels.create({
                    'hotel_name': name
                })
                partner = rp.search('name', '=', 'Best Day')
                if partner and partner.id:
                    p = hotels.search(['hotel_name', '=', name])
                    ps.create({
                        'name': partner.id,
                        'product_tmpl_id': p.product_id.product_tmpl_id.id
                    })
                else:
                    raise except_orm('Error', _("Partner error in api implementation"))
        return self.get_products('hotel')

    def get_products(self, _type):
        prod = self.env['product.' + _type]
        ps = self.env['product.supplierinfo']
        rp = self.env['res.partner']
        partner = rp.search('name', '=', 'Best Day')
        prods = [x.product_tmpl_id for x in ps.search([('name', '=', partner.id)])]
        return prod.search([('product_id.product_tmpl_id.id', 'in', prods)])

    def hotels_request(self, params):
        url = 'http://testxml.e-tsw.com/AffiliateService/AffiliateService.svc/restful/GetHotels'
        p = self.fill_credentials()
        p['c'] = ''
        p['sd'] = ''
        p['ed'] = ''
        p['h'] = ''
        p['rt'] = ''
        p['mp'] = ''
        p['r'] = ''
        p['d'] = ''
        p['l'] = ''
        p['hash'] = ''
        r = self.send_request(url, _dict=p)
        text = self.encode(r)

    def send_request(self, url, _dict):
        return requests.get(url, params=_dict)

    def encode(self, r):
        return r.text.encode('utf-8')

    def parse_countries(self, r, destinations):
        tree = etree.fromstring(self.encode(r))
        codes = []
        for x in tree:
            tmp = destinations.search([('name', '=', x[1].text)])
            if tmp and tmp.id:
                tmp.write({
                    'name': x[1].text,
                    'best_day_id': x[0].text
                })
            else:
                destinations.create({
                    'name': x[1].text,
                    'best_day_id': x[0].text
                })
            codes.append(x[0].text)
        return codes

    def parse_cities(self, r, destinations, code):
        tree = etree.fromstring(self.encode(r))
        parent = destinations.search([('best_day_id', '=', code)])
        if not (parent and parent.id):
            return
        for x in tree:
            if not x[0].text == '101':
                tmp = destinations.search([('name', '=', x[1].text)])
                if tmp and tmp.id:
                    tmp.write({
                        'name': x[1].text,
                        'best_day_id': x[0].text,
                        'parent_id': parent.id
                    })
                else:
                    destinations.create({
                        'name': x[1].text,
                        'best_day_id': x[0].text,
                        'parent_id': parent.id
                    })

    def get_destinations(self):
        params = self.fill_credentials()
        destinations = self.env['destination']
        dsts = destinations.search([('best_day_id', '!=', False)])
        params['ic'] = None
        destin_url = 'http://testxml.e-tsw.com/AffiliateService/AffiliateService.svc/restful/GetDestinations'
        country_url = 'http://testxml.e-tsw.com/AffiliateService/AffiliateService.svc/restful/GetCountries'
        if len(dsts):
            return dsts
        else:
            r = requests.get(country_url, params=self.fill_credentials())
            codes = self.parse_countries(r, destinations)
            for code in codes:
                params['ic'] = code
                r = requests.get(destin_url, params=params)
                self.parse_cities(r, destinations, code)
        dsts = destinations.search([('best_day_id', '!=', False)])
        return dsts


