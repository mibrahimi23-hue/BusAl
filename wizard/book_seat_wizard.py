from odoo import models, fields
from odoo.exceptions import UserError


class BookSeatWizard(models.TransientModel):
    _name = 'busal.book.seat.wizard'
    _description = 'Payment'

    booking_id = fields.Many2one('busal.booking', required=True)
    total_amount = fields.Float(related='booking_id.total_amount', string='Total')
    payment_method = fields.Selection([('card', 'Card'), ('cash', 'Cash')],
                                      string='Payment Method', default='card')
    card_number = fields.Char(string='Card Number')

    def action_pay(self):
        self.ensure_one()
        card = ''.join(c for c in (self.card_number or '') if c.isdigit())
        if self.payment_method == 'card' and len(card) != 16:
            raise UserError('Numri i kartës duhet të ketë 16 shifra.')
        self.booking_id._finalize(self.payment_method, card[-4:] if card else False)
        self.card_number = False
        return {
            'type': 'ir.actions.act_url',
            'url': '/busal/print/%s' % ','.join(str(i) for i in self.booking_id.ticket_ids.ids),
            'target': 'self',
        }