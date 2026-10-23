import string
from odoo import models, fields, api


class Bus(models.Model):
    _name = 'busal.bus'
    _description = 'Bus'
    _rec_name = 'plate_number'

    company_id = fields.Many2one('busal.company', string='Company', required=True)
    plate_number = fields.Char(string='Plate Number', required=True)
    model = fields.Char(string='Model')
    rows = fields.Integer(string='Rows (letters)', default=10)
    cols = fields.Integer(string='Seats per row', default=4)
    capacity = fields.Integer(string='Capacity', compute='_compute_capacity', store=True)
    bus_type = fields.Char(string='Bus Type')
    is_active = fields.Boolean(string='Active', default=True)
    created_at = fields.Datetime(string='Created At', default=fields.Datetime.now)
    updated_at = fields.Datetime(string='Updated At', default=fields.Datetime.now)

    seat_ids = fields.One2many('busal.seat', 'bus_id', string='Seats')
    trip_ids = fields.One2many('busal.trip', 'bus_id', string='Trips')

    @api.depends('rows', 'cols')
    def _compute_capacity(self):
        for b in self:
            b.capacity = b.rows * b.cols

    def action_generate_seats(self):
        for b in self:
            b.seat_ids.unlink()
            for r in range(min(b.rows, 26)):
                for c in range(1, b.cols + 1):
                    self.env['busal.seat'].create({
                        'bus_id': b.id,
                        'seat_number': string.ascii_uppercase[r] + str(c),
                    })

    @api.model_create_multi
    def create(self, vals_list):
        buses = super().create(vals_list)
        buses.action_generate_seats()
        return buses