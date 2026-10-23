from odoo import models, fields, api


class Customer(models.Model):
    _name = 'busal.customer'
    _description = 'Customer'
    _order = 'name'

    first_name = fields.Char(string='First Name', required=True)
    last_name = fields.Char(string='Last Name', required=True)
    name = fields.Char(compute='_compute_name', store=True)
    email = fields.Char(string='Email', required=True)
    phone = fields.Char(string='Phone')
    booking_ids = fields.One2many('busal.booking', 'customer_id', string='Bookings')
    booking_count = fields.Integer(string='Paid Bookings', compute='_compute_stats')
    total_spent = fields.Float(string='Total Spent', compute='_compute_stats')

    @api.depends('first_name', 'last_name')
    def _compute_name(self):
        for c in self:
            c.name = ('%s %s' % (c.first_name or '', c.last_name or '')).strip()

    @api.depends('booking_ids.status', 'booking_ids.total_amount')
    def _compute_stats(self):
        for c in self:
            paid = c.booking_ids.filtered(lambda b: b.status == 'paid')
            c.booking_count = len(paid)
            c.total_spent = sum(paid.mapped('total_amount'))