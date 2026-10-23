from odoo import models, fields


class SeatAvailability(models.Model):
    _name = 'busal.seat_availability'
    _description = 'Seat Availability'
    _rec_name = 'seat_number'

    trip_id = fields.Many2one('busal.trip', string='Trip', required=True, ondelete='cascade')
    seat_id = fields.Many2one('busal.seat', string='Seat', required=True)
    seat_number = fields.Char(related='seat_id.seat_number', store=True)
    status = fields.Selection([
        ('available', 'Available'),
        ('booked', 'Booked'),
        ('reserved', 'Reserved')
    ], string='Status', default='available')
    created_at = fields.Datetime(string='Created At', default=fields.Datetime.now)
    updated_at = fields.Datetime(string='Updated At', default=fields.Datetime.now)