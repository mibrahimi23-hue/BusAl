from odoo import models, fields


class City(models.Model):
    _name = 'busal.city'
    _description = 'City'

    name = fields.Char(string='Name', required=True)
    latitude = fields.Float(string='Latitude', digits=(10, 6))
    longitude = fields.Float(string='Longitude', digits=(10, 6))
    province = fields.Char(string='Province')
    latitude = fields.Float(string='Latitude')
    longitude = fields.Float(string='Longitude')
    created_at = fields.Datetime(string='Created At', default=fields.Datetime.now)

    origin_routes = fields.One2many('busal.route', 'origin_city_id', string='Origin Routes')
    destination_routes = fields.One2many('busal.route', 'destination_city_id', string='Destination Routes')