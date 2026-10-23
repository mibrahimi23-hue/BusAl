import json
from datetime import datetime, timedelta
import pytz
from odoo import models, fields, api
from odoo.exceptions import UserError
from .trip import TZ


class Booking(models.Model):
    _name = 'busal.booking'
    _description = 'Booking'
    _rec_name = 'booking_code'
    _order = 'id desc'

    user_id = fields.Many2one('busal.user', string='User')
    booking_code = fields.Char(string='Booking Code', required=True, copy=False,
                               default=lambda self: 'BK' + fields.Datetime.now().strftime('%y%m%d%H%M%S%f')[:15])
    customer_id = fields.Many2one('busal.customer', string='Customer')
    customer_name = fields.Char(related='customer_id.name', store=True, string='Customer Name')
    email = fields.Char(related='customer_id.email', string='Email')
    from_city_id = fields.Many2one('busal.city', string='From')
    to_city_id = fields.Many2one('busal.city', string='To')
    trip_date = fields.Date(string='Date', default=lambda self: fields.Date.context_today(self))
    schedule_id = fields.Many2one('busal.schedule', string='Departure')
    trip_id = fields.Many2one('busal.trip', string='Trip')
    bus_id = fields.Many2one(related='schedule_id.bus_id', string='Bus')
    company_id = fields.Many2one(related='schedule_id.company_id', store=True, string='Company')
    route_id = fields.Many2one('busal.route', compute='_compute_route', store=True, string='Route')
    departure_time = fields.Datetime(compute='_compute_info', string='Departure Time')
    arrival_time = fields.Datetime(compute='_compute_info', string='Arrival Time')
    base_price = fields.Float(compute='_compute_info', string='Price per Seat')
    passenger_count = fields.Integer(string='Passengers', default=1)
    selected_seats = fields.Char(string='Seats')
    seat_data = fields.Text(compute='_compute_seat_data')
    passenger_names = fields.Text(string='Passenger names')
    card_last4 = fields.Char(string='Card (last 4)')
    status = fields.Selection([
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='pending')
    total_amount = fields.Float(string='Total Amount', compute='_compute_total', store=True)
    created_at = fields.Datetime(string='Created At', default=fields.Datetime.now)
    updated_at = fields.Datetime(string='Updated At', default=fields.Datetime.now)

    ticket_ids = fields.One2many('busal.ticket', 'booking_id', string='Tickets')
    payment_ids = fields.One2many('busal.payment', 'booking_id', string='Payments')

    def _booked_numbers(self):
        self.ensure_one()
        trip = self.env['busal.trip'].sudo().search([
            ('schedule_id', '=', self.schedule_id.id),
            ('trip_date', '=', self.trip_date),
        ], limit=1)
        if not trip:
            return set()
        taken = trip.seat_availability_ids.filtered(lambda a: a.status != 'available')
        return set(taken.mapped('seat_id.seat_number'))

    def _seat_names(self):
        names = []
        for x in (self.selected_seats or '').split(','):
            x = x.strip().upper()
            if x and x not in names:
                names.append(x)
        return names

    def _selected_seat_records(self):
        if not self.schedule_id:
            return self.env['busal.seat']
        return self.env['busal.seat'].search([
            ('bus_id', '=', self.schedule_id.bus_id.id),
            ('seat_number', 'in', self._seat_names()),
        ])

    def _passenger_list(self):
        names = [n.strip() for n in (self.passenger_names or '').splitlines() if n.strip()]
        if not names and self.passenger_count == 1 and self.customer_id:
            names = [self.customer_id.name]
        return names

    @api.depends('schedule_id', 'trip_date')
    def _compute_seat_data(self):
        for b in self:
            data = []
            if b.schedule_id and b.trip_date:
                booked = b._booked_numbers()
                for s in b.schedule_id.bus_id.seat_ids:
                    data.append({'n': s.seat_number, 'b': s.seat_number in booked})
            b.seat_data = json.dumps(data)

    @api.depends('from_city_id', 'to_city_id')
    def _compute_route(self):
        Route = self.env['busal.route'].sudo()
        for b in self:
            route = False
            if b.from_city_id and b.to_city_id and b.from_city_id != b.to_city_id:
                domain = [('origin_city_id', '=', b.from_city_id.id),
                          ('destination_city_id', '=', b.to_city_id.id)]
                route = Route.search(domain, limit=1) or Route.create({
                    'origin_city_id': b.from_city_id.id,
                    'destination_city_id': b.to_city_id.id,
                })
            b.route_id = route

    @api.depends('trip_date', 'schedule_id.departure_hour', 'route_id.duration_min',
                 'route_id.distance_km', 'route_id.price_per_km')
    def _compute_info(self):
        for b in self:
            dep = False
            if b.trip_date and b.schedule_id:
                minutes = int(round(b.schedule_id.departure_hour * 60))
                local = datetime(b.trip_date.year, b.trip_date.month, b.trip_date.day) + timedelta(minutes=minutes)
                dep = TZ.localize(local).astimezone(pytz.utc).replace(tzinfo=None)
            b.departure_time = dep
            b.arrival_time = dep + timedelta(minutes=b.route_id.duration_min) if dep else False
            b.base_price = b.route_id.distance_km * b.route_id.price_per_km

    @api.depends('ticket_ids.price', 'selected_seats', 'schedule_id',
                 'route_id.distance_km', 'route_id.price_per_km')
    def _compute_total(self):
        for b in self:
            if b.ticket_ids:
                b.total_amount = sum(b.ticket_ids.mapped('price'))
            else:
                price = b.route_id.distance_km * b.route_id.price_per_km
                b.total_amount = sum(price + s.price for s in b._selected_seat_records())

    @api.onchange('from_city_id', 'to_city_id')
    def _onchange_cities(self):
        self.schedule_id = False
        self.selected_seats = False

    @api.onchange('schedule_id', 'trip_date', 'passenger_count')
    def _onchange_seats(self):
        self.selected_seats = False

    def _get_trip(self):
        s = self.schedule_id
        Trip = self.env['busal.trip'].sudo()
        trip = Trip.search([('schedule_id', '=', s.id), ('trip_date', '=', self.trip_date)], limit=1)
        if not trip:
            trip = Trip.create({
                'schedule_id': s.id,
                'trip_date': self.trip_date,
                'bus_id': s.bus_id.id,
                'company_id': s.company_id.id,
                'from_city_id': s.from_city_id.id,
                'to_city_id': s.to_city_id.id,
            })
        return trip

    def action_confirm(self):
        self.ensure_one()
        if not (self.schedule_id and self.trip_date):
            raise UserError('Zgjidh datën dhe orarin.')
        if self.passenger_count < 1:
            raise UserError('Numri i pasagjerëve duhet të jetë të paktën 1.')
        names = self._seat_names()
        if len(names) != self.passenger_count:
            raise UserError('Zgjidh saktësisht %s vende.' % self.passenger_count)
        seats = self._selected_seat_records()
        if len(seats) != len(names):
            raise UserError('Një nga vendet nuk ekziston në këtë autobus.')
        if not self.customer_id:
            raise UserError('Zgjidh ose krijo klientin (Customer).')
        if len(self._passenger_list()) != self.passenger_count:
            raise UserError('Shkruaj %s emra pasagjerësh, një për rresht.' % self.passenger_count)
        trip = self._get_trip()
        if trip.departure_time and trip.departure_time < fields.Datetime.now():
            raise UserError('Ky udhëtim ka ikur tashmë, zgjidh një datë ose orar tjetër.')
        av = self.env['busal.seat_availability'].search([
            ('trip_id', '=', trip.id), ('seat_id', 'in', seats.ids)])
        if len(av) != len(seats) or any(a.status != 'available' for a in av):
            raise UserError('Një nga vendet është i zënë, zgjidh përsëri.')
        self.trip_id = trip
        return {
            'type': 'ir.actions.act_window',
            'name': 'Payment',
            'res_model': 'busal.book.seat.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_booking_id': self.id},
        }

    def _finalize(self, method, card_last4):
        self.ensure_one()
        order = self._seat_names()
        seats = sorted(self._selected_seat_records(), key=lambda s: order.index(s.seat_number))
        for name, seat in zip(self._passenger_list(), seats):
            self.env['busal.ticket'].create({
                'booking_id': self.id,
                'trip_id': self.trip_id.id,
                'seat_id': seat.id,
                'passenger_name': name,
            })
        self.card_last4 = card_last4
        payment = self.env['busal.payment'].create({
            'booking_id': self.id,
            'payment_method': method,
            'amount': self.total_amount,
        })
        payment.action_pay()

    def action_print(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': '/busal/print/%s' % ','.join(str(i) for i in self.ticket_ids.ids),
            'target': 'self',
        }

    def action_cancel(self):
        for b in self:
            b.status = 'cancelled'
            for t in b.ticket_ids:
                self.env['busal.seat_availability'].search(
                    [('trip_id', '=', t.trip_id.id), ('seat_id', '=', t.seat_id.id)]
                ).write({'status': 'available'})