from odoo import models, fields, api


class Schedule(models.Model):
    _name = 'busal.schedule'
    _description = 'Bus Schedule'

    name = fields.Char(compute='_compute_name', store=True)
    bus_id = fields.Many2one('busal.bus', string='Bus', required=True)
    company_id = fields.Many2one(related='bus_id.company_id', store=True, string='Company')
    from_city_id = fields.Many2one('busal.city', string='From', required=True)
    to_city_id = fields.Many2one('busal.city', string='To', required=True)
    departure_hour = fields.Float(string='Departure Time')
    active = fields.Boolean(default=True)

    @api.depends('departure_hour', 'from_city_id', 'to_city_id',
                 'bus_id.plate_number', 'bus_id.company_id.name')
    def _compute_name(self):
        for s in self:
            h, m = divmod(int(round(s.departure_hour * 60)), 60)
            s.name = '%02d:%02d  %s - %s  (%s, %s)' % (
                h, m, s.from_city_id.name or '', s.to_city_id.name or '',
                s.bus_id.company_id.name or '', s.bus_id.plate_number or '')

    def action_generate_schedules(self):
        cities = self.env['busal.city'].search([])
        buses = self.env['busal.bus'].search([], order='id')
        if not buses:
            return {'type': 'ir.actions.client', 'tag': 'reload'}
        hours = [7.0, 10.0, 14.0, 18.0, 20.5]
        existing = {}
        for s in self.search([]):
            existing.setdefault((s.from_city_id.id, s.to_city_id.id), set()).add(s.departure_hour)
        vals = []
        i = 0
        for a in cities:
            for b in cities:
                if a == b:
                    continue
                used = existing.get((a.id, b.id), set())
                for h in hours:
                    if len(used) >= 4:
                        break
                    if h in used:
                        continue
                    used.add(h)
                    vals.append({
                        'bus_id': buses[i % len(buses)].id,
                        'from_city_id': a.id,
                        'to_city_id': b.id,
                        'departure_hour': h,
                    })
                    i += 1
        if vals:
            self.create(vals)
        return {'type': 'ir.actions.client', 'tag': 'reload'}