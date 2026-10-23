from odoo import models, fields


class Seat(models.Model):
    _name = 'busal.seat'
    _description = 'Seat'
    _rec_name = 'seat_number'

    bus_id = fields.Many2one('busal.bus', string='Bus', required=True)
    seat_number = fields.Char(string='Seat Number', required=True)
    seat_type = fields.Char(string='Seat Type')
    price = fields.Float(string='Extra Price')
    is_active = fields.Boolean(string='Active', default=True)

    seat_availability_ids = fields.One2many('busal.seat_availability', 'seat_id', string='Availability')