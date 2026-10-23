import math
from odoo import models, fields, api


class Route(models.Model):
    _name = 'busal.route'
    _description = 'Route'

    name = fields.Char(compute='_compute_name', store=True)
    origin_city_id = fields.Many2one('busal.city', string='Origin City', required=True)
    destination_city_id = fields.Many2one('busal.city', string='Destination City', required=True)
    distance_km = fields.Float(string='Distance (km)', compute='_compute_distance', store=True, readonly=False)
    avg_speed = fields.Float(string='Avg Speed (km/h)', default=60)
    duration_min = fields.Integer(string='Duration (minutes)', compute='_compute_duration', store=True, readonly=False)
    price_per_km = fields.Float(string='Price per km', default=0.1)
    is_active = fields.Boolean(string='Active', default=True)
    created_at = fields.Datetime(string='Created At', default=fields.Datetime.now)
    updated_at = fields.Datetime(string='Updated At', default=fields.Datetime.now)

    trip_ids = fields.One2many('busal.trip', 'route_id', string='Trips')

    @api.depends('origin_city_id', 'destination_city_id')
    def _compute_name(self):
        for r in self:
            r.name = '%s - %s' % (r.origin_city_id.name or '', r.destination_city_id.name or '')

    @api.depends('origin_city_id.latitude', 'origin_city_id.longitude',
                 'destination_city_id.latitude', 'destination_city_id.longitude')
    def _compute_distance(self):
        for r in self:
            a, b = r.origin_city_id, r.destination_city_id
            if a and b:
                lat1, lon1, lat2, lon2 = map(math.radians, [a.latitude, a.longitude, b.latitude, b.longitude])
                h = (math.sin((lat2 - lat1) / 2) ** 2
                     + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2)
                r.distance_km = round(6371 * 2 * math.asin(math.sqrt(h)) * 1.3, 1)
            else:
                r.distance_km = 0

    @api.depends('distance_km', 'avg_speed')
    def _compute_duration(self):
        for r in self:
            r.duration_min = int(r.distance_km / r.avg_speed * 60) if r.avg_speed else 0

    def action_generate_routes(self):
        cities = self.env['busal.city'].search([])
        for a in cities:
            for b in cities:
                if a != b and not self.search([('origin_city_id', '=', a.id),
                                               ('destination_city_id', '=', b.id)], limit=1):
                    self.create({'origin_city_id': a.id, 'destination_city_id': b.id})
        return {'type': 'ir.actions.client', 'tag': 'reload'}