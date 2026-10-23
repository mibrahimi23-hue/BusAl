from odoo import models, fields, api
from odoo.exceptions import ValidationError


class Ticket(models.Model):
    _name = 'busal.ticket'
    _description = 'Ticket'
    _rec_name = 'ticket_number'

    ticket_number = fields.Char(compute='_compute_number', store=True)
    booking_id = fields.Many2one('busal.booking', string='Booking', required=True)
    trip_id = fields.Many2one('busal.trip', string='Trip', required=True)
    seat_id = fields.Many2one('busal.seat', string='Seat', required=True)
    passenger_name = fields.Char(string='Passenger')
    company_id = fields.Many2one(related='trip_id.company_id', string='Company')
    bus_id = fields.Many2one(related='trip_id.bus_id', string='Bus')
    origin = fields.Char(related='trip_id.origin', string='From')
    destination = fields.Char(related='trip_id.destination', string='To')
    departure_time = fields.Datetime(related='trip_id.departure_time')
    arrival_time = fields.Datetime(related='trip_id.arrival_time')
    customer_name = fields.Char(related='booking_id.customer_name', string='Customer')
    customer_email = fields.Char(related='booking_id.email', string='Email')
    price = fields.Float(string='Price', compute='_compute_price', store=True)
    tickets_load = fields.Char(string='Ticket Load')
    created_at = fields.Datetime(string='Created At', default=fields.Datetime.now)

    @api.depends('booking_id.booking_code', 'seat_id.seat_number')
    def _compute_number(self):
        for t in self:
            t.ticket_number = '%s-%s' % (t.booking_id.booking_code or '', t.seat_id.seat_number or '')

    @api.depends('trip_id.base_price', 'seat_id.price')
    def _compute_price(self):
        for t in self:
            t.price = t.trip_id.base_price + t.seat_id.price

    def action_print(self):
        return {
            'type': 'ir.actions.act_url',
            'url': '/busal/print/%s' % ','.join(str(i) for i in self.ids),
            'target': 'self',
        }

    @api.model_create_multi
    def create(self, vals_list):
        tickets = super().create(vals_list)
        for t in tickets:
            av = self.env['busal.seat_availability'].search(
                [('trip_id', '=', t.trip_id.id), ('seat_id', '=', t.seat_id.id)], limit=1)
            if not av or av.status != 'available':
                raise ValidationError('Ky vend është i zënë.')
            av.status = 'booked'
        return tickets