from datetime import datetime, timedelta
import pytz
from odoo import models, fields, api
from odoo.exceptions import ValidationError

TZ = pytz.timezone('Europe/Tirane')


class Trip(models.Model):
    _name = 'busal.trip'
    _description = 'Trip'
    _order = 'departure_time'

    name = fields.Char(compute='_compute_name', store=True)
    from_city_id = fields.Many2one('busal.city', string='From', required=True)
    to_city_id = fields.Many2one('busal.city', string='To', required=True)
    company_id = fields.Many2one('busal.company', string='Company', required=True)
    bus_id = fields.Many2one('busal.bus', string='Bus', required=True)
    schedule_id = fields.Many2one('busal.schedule', string='Schedule', required=True)
    trip_date = fields.Date(string='Date', required=True,
                            default=lambda self: datetime.now(TZ).date())
    allowed_company_ids = fields.Many2many('busal.company', compute='_compute_allowed')
    allowed_bus_ids = fields.Many2many('busal.bus', compute='_compute_allowed')
    route_id = fields.Many2one('busal.route', string='Route', compute='_compute_route', store=True)
    origin = fields.Char(related='from_city_id.name', string='From City')
    destination = fields.Char(related='to_city_id.name', string='To City')
    departure_time = fields.Datetime(string='Departure Time', compute='_compute_departure', store=True)
    arrival_time = fields.Datetime(string='Arrival Time', compute='_compute_arrival', store=True)
    base_price = fields.Float(string='Price per Seat', compute='_compute_price', store=True, readonly=False)
    available_seats = fields.Integer(string='Available Seats', compute='_compute_seats')
    seat_map = fields.Html(compute='_compute_seat_map', sanitize=False)
    status = fields.Selection([
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='scheduled')
    created_at = fields.Datetime(string='Created At', default=fields.Datetime.now)
    updated_at = fields.Datetime(string='Updated At', default=fields.Datetime.now)

    ticket_ids = fields.One2many('busal.ticket', 'trip_id', string='Tickets')
    seat_availability_ids = fields.One2many('busal.seat_availability', 'trip_id', string='Seat Availability')
    review_ids = fields.One2many('busal.review', 'trip_id', string='Reviews')

    @api.depends('from_city_id', 'to_city_id', 'company_id')
    def _compute_allowed(self):
        Schedule = self.env['busal.schedule']
        for t in self:
            schedules = Schedule.browse()
            if t.from_city_id and t.to_city_id:
                schedules = Schedule.search([('from_city_id', '=', t.from_city_id.id),
                                             ('to_city_id', '=', t.to_city_id.id)])
            t.allowed_company_ids = schedules.mapped('company_id')
            buses = schedules.mapped('bus_id')
            if t.company_id:
                buses = buses.filtered(lambda b: b.company_id == t.company_id)
            t.allowed_bus_ids = buses

    @api.constrains('schedule_id', 'bus_id', 'from_city_id', 'to_city_id')
    def _check_schedule(self):
        for t in self:
            s = t.schedule_id
            if s.bus_id != t.bus_id or s.from_city_id != t.from_city_id or s.to_city_id != t.to_city_id:
                raise ValidationError('Orari nuk i përket këtij busi dhe kësaj linje.')

    @api.depends('trip_date', 'schedule_id')
    def _compute_name(self):
        for t in self:
            t.name = '%s  %s' % (t.trip_date or '', t.schedule_id.name or '')

    @api.depends('trip_date', 'schedule_id.departure_hour')
    def _compute_departure(self):
        for t in self:
            if t.trip_date and t.schedule_id:
                minutes = int(round(t.schedule_id.departure_hour * 60))
                local = datetime(t.trip_date.year, t.trip_date.month, t.trip_date.day) + timedelta(minutes=minutes)
                t.departure_time = TZ.localize(local).astimezone(pytz.utc).replace(tzinfo=None)
            else:
                t.departure_time = False

    @api.depends('from_city_id', 'to_city_id')
    def _compute_route(self):
        Route = self.env['busal.route'].sudo()
        for t in self:
            route = False
            if t.from_city_id and t.to_city_id:
                domain = [('origin_city_id', '=', t.from_city_id.id),
                          ('destination_city_id', '=', t.to_city_id.id)]
                route = Route.search(domain, limit=1)
                if not route:
                    route = Route.create({
                        'origin_city_id': t.from_city_id.id,
                        'destination_city_id': t.to_city_id.id,
                    })
            t.route_id = route

    @api.depends('departure_time', 'route_id.duration_min')
    def _compute_arrival(self):
        for t in self:
            if t.departure_time:
                t.arrival_time = t.departure_time + timedelta(minutes=t.route_id.duration_min)
            else:
                t.arrival_time = False

    @api.depends('route_id.distance_km', 'route_id.price_per_km')
    def _compute_price(self):
        for t in self:
            t.base_price = t.route_id.distance_km * t.route_id.price_per_km

    @api.depends('bus_id.seat_ids', 'seat_availability_ids.status')
    def _compute_seats(self):
        for t in self:
            booked = t.seat_availability_ids.filtered(lambda a: a.status != 'available')
            t.available_seats = len(t.bus_id.seat_ids) - len(booked)

    @api.depends('bus_id', 'seat_availability_ids.status')
    def _compute_seat_map(self):
        for t in self:
            status = {a.seat_id.id: a.status for a in t.seat_availability_ids}
            rows = {}
            for seat in t.bus_id.seat_ids:
                rows.setdefault((seat.seat_number or '?')[:1], []).append(seat)
            html = ''
            for letter in sorted(rows):
                seats = sorted(rows[letter], key=lambda s: (len(s.seat_number), s.seat_number))
                html += '<div><b style="display:inline-block;width:24px">%s</b>' % letter
                for i, s in enumerate(seats):
                    free = status.get(s.id, 'available') == 'available'
                    color = '#28a745' if free else '#dc3545'
                    gap = 'margin-right:28px;' if i == 1 else ''
                    html += ('<span style="display:inline-block;width:46px;margin:3px;padding:6px 0;'
                             'text-align:center;color:#fff;border-radius:4px;%sbackground:%s">%s</span>'
                             % (gap, color, s.seat_number))
                html += '</div>'
            t.seat_map = html

    @api.onchange('from_city_id', 'to_city_id')
    def _onchange_cities(self):
        self.company_id = False
        self.bus_id = False
        self.schedule_id = False

    @api.onchange('company_id')
    def _onchange_company(self):
        self.bus_id = False
        self.schedule_id = False

    @api.onchange('bus_id')
    def _onchange_bus(self):
        self.schedule_id = False

    def _generate_seats(self):
        vals = []
        for t in self:
            existing = t.seat_availability_ids.mapped('seat_id')
            for seat in t.bus_id.seat_ids - existing:
                vals.append({'trip_id': t.id, 'seat_id': seat.id})
        if vals:
            self.env['busal.seat_availability'].create(vals)

    def action_book_seat(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'New Booking',
            'res_model': 'busal.booking',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_trip_id': self.id,
                'default_schedule_id': self.schedule_id.id,
                'default_from_city_id': self.from_city_id.id,
                'default_to_city_id': self.to_city_id.id,
                'default_trip_date': str(self.trip_date),
            },
        }

    def action_start(self):
        self.status = 'ongoing'

    def action_complete(self):
        self.status = 'completed'

    def action_cancel(self):
        self.status = 'cancelled'

    @api.model_create_multi
    def create(self, vals_list):
        trips = super().create(vals_list)
        trips._generate_seats()
        return trips