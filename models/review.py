from odoo import models, fields


class Review(models.Model):
    _name = 'busal.review'
    _description = 'Review'

    user_id = fields.Many2one('busal.user', string='User', required=True)
    trip_id = fields.Many2one('busal.trip', string='Trip', required=True)
    rating = fields.Integer(string='Rating')
    comment = fields.Text(string='Comment')
    created_at = fields.Datetime(string='Created At', default=fields.Datetime.now)
    updated_at = fields.Datetime(string='Updated At', default=fields.Datetime.now)