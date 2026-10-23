import pytz
from markupsafe import Markup, escape
from odoo import api, fields, models


class BusalBooking(models.Model):
    _inherit = 'busal.booking'

    route_card = fields.Html(compute='_compute_route_card', sanitize=False)

    def _route_card_html(self):
        self.ensure_one()
        if not (self.departure_time and self.arrival_time):
            return Markup('')
        tz = pytz.timezone('Europe/Tirane')
        dep = pytz.utc.localize(self.departure_time).astimezone(tz)
        arr = pytz.utc.localize(self.arrival_time).astimezone(tz)
        mins = int((self.arrival_time - self.departure_time).total_seconds() // 60)
        duration = '%dh %02dm' % (mins // 60, mins % 60)
        frm = escape(self.from_city_id.name or '')
        to = escape(self.to_city_id.name or '')
        info = escape(' · '.join(x for x in [self.company_id.name, self.bus_id.display_name] if x))
        return Markup(
            '<div style="border:1px solid #dee2e6;border-radius:12px;padding:16px 20px;">'
            '<div style="display:flex;align-items:center;justify-content:space-between;">'
            '<div><div style="font-size:1.3rem;font-weight:600;">%s</div>'
            '<div style="font-size:2rem;font-weight:700;">%s</div>'
            '<div style="opacity:.7;">%s</div></div>'
            '<div style="flex:1;text-align:center;padding:0 16px;">'
            '<div style="opacity:.7;">%s</div>'
            '<div style="border-top:2px solid #714B67;margin:6px 0;"></div>'
            '<div style="opacity:.7;">🚌 %s</div></div>'
            '<div style="text-align:right;"><div style="font-size:1.3rem;font-weight:600;">%s</div>'
            '<div style="font-size:2rem;font-weight:700;">%s</div>'
            '<div style="opacity:.7;">%s</div></div>'
            '</div></div>'
        ) % (frm, dep.strftime('%H:%M'), dep.strftime('%d.%m.%Y'),
             duration, info,
             to, arr.strftime('%H:%M'), arr.strftime('%d.%m.%Y'))

    @api.depends('departure_time', 'arrival_time', 'from_city_id', 'to_city_id',
                 'company_id', 'bus_id')
    def _compute_route_card(self):
        for b in self:
            b.route_card = b._route_card_html()