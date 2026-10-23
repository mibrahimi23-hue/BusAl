/** @odoo-module **/
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { Component, xml } from "@odoo/owl";

export class SeatMapPicker extends Component {
    static template = xml`
        <div>
            <div t-if="!seats.length" style="color:#6c757d;">Zgjidh nisjen per te pare vendet.</div>
            <div t-foreach="rows" t-as="row" t-key="row.letter">
                <b style="display:inline-block;width:24px;" t-esc="row.letter"/>
                <t t-foreach="row.seats" t-as="s" t-key="s.n">
                    <span t-att-style="seatStyle(s, s_index)" t-on-click="() => this.select(s)" t-esc="s.n"/>
                </t>
            </div>
            <div style="margin-top:8px;">
                <span style="color:#28a745;">E lire</span>
                <span style="color:#dc3545;margin-left:12px;">E zene</span>
                <span style="color:#007bff;margin-left:12px;">E zgjedhur</span>
            </div>
            <div style="margin-top:6px;">
                Zgjedhur: <b t-esc="selected.join(', ') || '-'"/> (<t t-esc="selected.length"/>/<t t-esc="limit"/>)
            </div>
        </div>`;
    static props = { ...standardFieldProps };

    get seats() {
        try {
            return JSON.parse(this.props.record.data.seat_data || "[]");
        } catch (e) {
            return [];
        }
    }

    get rows() {
        const rows = {};
        for (const s of this.seats) {
            const letter = (s.n || "?")[0];
            if (!rows[letter]) {
                rows[letter] = [];
            }
            rows[letter].push(s);
        }
        return Object.keys(rows)
            .sort()
            .map((letter) => ({
                letter,
                seats: rows[letter].sort((a, b) =>
                    a.n.localeCompare(b.n, undefined, { numeric: true })
                ),
            }));
    }

    get selected() {
        const v = this.props.record.data[this.props.name] || "";
        return v.split(",").map((x) => x.trim()).filter((x) => x);
    }

    get limit() {
        return this.props.record.data.passenger_count || 1;
    }

    seatStyle(seat, index) {
        let color = "#28a745";
        if (seat.b) {
            color = "#dc3545";
        } else if (this.selected.includes(seat.n)) {
            color = "#007bff";
        }
        const cursor = seat.b ? "not-allowed" : "pointer";
        const aisle = index === 1 ? "margin-right:28px;" : "";
        return (
            "display:inline-block;width:46px;margin:3px;padding:8px 0;text-align:center;" +
            "color:#fff;border-radius:6px;font-weight:bold;" +
            aisle + "background:" + color + ";cursor:" + cursor + ";"
        );
    }

    select(seat) {
        if (seat.b || this.props.readonly) {
            return;
        }
        let names = this.selected;
        if (names.includes(seat.n)) {
            names = names.filter((x) => x !== seat.n);
        } else if (names.length < this.limit) {
            names.push(seat.n);
        } else {
            return;
        }
        this.props.record.update({ [this.props.name]: names.join(",") });
    }
}

registry.category("fields").add("busal_seat_map", {
    component: SeatMapPicker,
    supportedTypes: ["char"],
});
