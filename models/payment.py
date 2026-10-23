from odoo import models, fields, api


class Payment(models.Model):
    _name = 'busal.payment'
    _description = 'Payment'
    _order = 'id desc'

    booking_id = fields.Many2one('busal.booking', string='Booking', required=True)
    customer_name = fields.Char(related='booking_id.customer_name', string='Customer')
    company_id = fields.Many2one(related='booking_id.company_id', store=True, string='Company')
    route_id = fields.Many2one(related='booking_id.route_id', store=True, string='Route')
    passengers = fields.Integer(related='booking_id.passenger_count', store=True, string='Passengers')
    payment_method = fields.Selection([('card', 'Card'), ('cash', 'Cash')], string='Payment Method')
    amount = fields.Float(string='Amount')
    currency = fields.Char(string='Currency', default='EUR')
    status = fields.Selection([
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ], string='Status', default='pending')
    paid_at = fields.Datetime(string='Paid At')
    created_at = fields.Datetime(string='Created At', default=fields.Datetime.now)

    @api.onchange('booking_id')
    def _onchange_booking(self):
        self.amount = self.booking_id.total_amount

    def action_pay(self):
        for p in self:
            p.status = 'completed'
            p.paid_at = fields.Datetime.now()
            p.booking_id.status = 'paid'