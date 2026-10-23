import io
import re
from html import escape
import pytz
from odoo import http
from odoo.http import request
from odoo.addons.busal.models.trip import TZ

try:
    import qrcode
    import qrcode.image.svg
except ImportError:
    qrcode = None


def fmt(dt):
    if not dt:
        return ''
    return pytz.utc.localize(dt).astimezone(TZ).strftime('%d/%m/%Y %H:%M')


def qr_svg(text):
    if not qrcode:
        return ''
    img = qrcode.make(text, image_factory=qrcode.image.svg.SvgPathImage, box_size=10, border=2)
    buf = io.BytesIO()
    img.save(buf)
    svg = buf.getvalue().decode()
    svg = svg[svg.index('<svg'):]
    return re.sub(r'width="[^"]*" height="[^"]*"', 'width="150" height="150"', svg, 1)


STYLE = (
    'body{font-family:Arial,sans-serif;max-width:700px;margin:20px auto;}'
    'table{border-collapse:collapse;width:100%;}'
    'td{border:1px solid #999;padding:6px 10px;}'
    'td:first-child{background:#f0f0f0;width:200px;}'
    'button,a.btn{padding:8px 16px;margin-right:8px;font-size:14px;cursor:pointer;}'
    'a.btn{border:1px solid #999;text-decoration:none;color:#000;display:inline-block;}'
    '.ticket{page-break-after:always;margin-bottom:40px;}'
    '.route{border:2px solid #714B67;border-radius:12px;padding:16px 20px;margin:12px 0 20px;}'
    '.route .row{display:flex;align-items:center;justify-content:space-between;}'
    '.route .city{font-size:18px;font-weight:bold;}'
    '.route .time{font-size:32px;font-weight:bold;}'
    '.route .date{color:#666;}'
    '.route .mid{flex:1;text-align:center;padding:0 16px;color:#666;}'
    '.route .line{border-top:2px solid #714B67;margin:6px 0;}'
    '.route .foot{margin-top:12px;color:#444;text-align:center;}'
    '.qr{text-align:center;margin-top:20px;}'
    '.qr div{color:#666;font-size:12px;margin-top:4px;}'
    '@media print{.noprint{display:none;}}'
)


def route_card(t):
    dep, arr = t.departure_time, t.arrival_time
    if not (dep and arr):
        return ''
    d = pytz.utc.localize(dep).astimezone(TZ)
    a = pytz.utc.localize(arr).astimezone(TZ)
    mins = int((arr - dep).total_seconds() // 60)
    duration = '%dh %02dm' % (mins // 60, mins % 60)
    info = ' · '.join(x for x in [t.company_id.name, t.bus_id.plate_number] if x)
    return (
        '<div class="route"><div class="row">'
        '<div><div class="city">' + escape(t.origin or '') + '</div>'
        '<div class="time">' + d.strftime('%H:%M') + '</div>'
        '<div class="date">' + d.strftime('%d.%m.%Y') + '</div></div>'
        '<div class="mid"><div>' + duration + '</div><div class="line"></div>'
        '<div>&#9654;</div></div>'
        '<div style="text-align:right"><div class="city">' + escape(t.destination or '') + '</div>'
        '<div class="time">' + a.strftime('%H:%M') + '</div>'
        '<div class="date">' + a.strftime('%d.%m.%Y') + '</div></div>'
        '</div><div class="foot">' + escape(info) + '</div></div>'
    )


def qr_text(t):
    b = t.booking_id
    info = ' · '.join(x for x in [t.company_id.name, t.bus_id.plate_number] if x)
    lines = [
        'BUS AL',
        'Booking: %s' % (b.booking_code or ''),
        'Ticket: %s' % (t.ticket_number or ''),
        'Passenger: %s' % (t.passenger_name or ''),
        '%s -> %s' % (t.origin or '', t.destination or ''),
        'Nisja: %s' % fmt(t.departure_time),
        'Arritja: %s' % fmt(t.arrival_time),
        info,
        'Vendi: %s' % (t.seat_id.seat_number or ''),
        'Cmimi biletes: %.2f EUR' % t.price,
        'Totali: %.2f EUR' % b.total_amount,
    ]
    return '\n'.join(x for x in lines if x)


class TicketController(http.Controller):

    def _page(self, t):
        b = t.booking_id
        pay = b.payment_ids[:1]
        method = (pay.payment_method or '').capitalize()
        if b.card_last4:
            method += ' **** ' + b.card_last4
        rows = [
            ('Ticket No.', t.ticket_number),
            ('Booking', b.booking_code),
            ('Passenger', t.passenger_name),
            ('Customer', b.customer_name),
            ('Email', b.email),
            ('Company', t.company_id.name),
            ('Bus', t.bus_id.plate_number),
            ('Seat', t.seat_id.seat_number),
            ('Price per seat', '%.2f EUR' % t.trip_id.base_price),
            ('Seat supplement', '%.2f EUR' % t.seat_id.price),
            ('Ticket price', '%.2f EUR' % t.price),
            ('Payment', method),
            ('Paid at', fmt(pay.paid_at)),
            ('Status', b.status),
        ]
        html = '<div class="ticket"><h2>BUS AL - Ticket &amp; Invoice</h2>' + route_card(t) + '<table>'
        for label, value in rows:
            html += '<tr><td>' + escape(label) + '</td><td>' + escape(str(value or '')) + '</td></tr>'
        html += '</table><h3>Total booking: ' + ('%.2f EUR' % b.total_amount) + '</h3>'
        qr = qr_svg(qr_text(t))
        if qr:
            html += '<div class="qr">' + qr + '<div>' + escape(str(t.ticket_number or '')) + '</div></div>'
        html += '</div>'
        return html

    @http.route('/busal/print/<string:ids>', type='http', auth='user')
    def print_tickets(self, ids, **kw):
        id_list = [int(i) for i in ids.split(',') if i.isdigit()]
        tickets = request.env['busal.ticket'].browse(id_list).exists()
        pages = ''.join(self._page(t) for t in tickets)
        html = (
            '<!DOCTYPE html><html><head><meta charset="utf-8"><title>Ticket / Invoice</title>'
            '<style>' + STYLE + '</style></head><body>'
            '<div class="noprint"><button onclick="window.print()">Print</button>'
            '<a class="btn" href="/web#model=busal.booking&view_type=list">Back to Bookings</a></div>'
            + pages + '</body></html>'
        )
        return request.make_response(html, headers=[('Content-Type', 'text/html; charset=utf-8')])