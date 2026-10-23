from odoo import models, fields


class User(models.Model):
    _name = 'busal.user'
    _description = 'User'

    name = fields.Char(string='Name', required=True)
    email = fields.Char(string='Email', required=True)
    password = fields.Char(string='Password')
    phone = fields.Char(string='Phone')
    is_active = fields.Boolean(string='Active', default=True)
    created_at = fields.Datetime(string='Created At', default=fields.Datetime.now)
    updated_at = fields.Datetime(string='Updated At', default=fields.Datetime.now)

    booking_ids = fields.One2many('busal.booking', 'user_id', string='Bookings')
    review_ids = fields.One2many('busal.review', 'user_id', string='Reviews')