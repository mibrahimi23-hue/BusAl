from odoo import models, fields


class Company(models.Model):
    _name = 'busal.company'
    _description = 'Company'

    name = fields.Char(string='Company Name', required=True)
    logo_url = fields.Char(string='Logo URL')
    phone = fields.Char(string='Phone')
    email = fields.Char(string='Email')
    address = fields.Char(string='Address')
    created_at = fields.Datetime(string='Created At', default=fields.Datetime.now)
    updated_at = fields.Datetime(string='Updated At', default=fields.Datetime.now)

    bus_ids = fields.One2many('busal.bus', 'company_id', string='Buses')
    trip_ids = fields.One2many('busal.trip', 'company_id', string='Trips')