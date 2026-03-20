# Copyright (c) 2025, HealVN Team and contributors
# For license information, please see license.txt

"""
HealVN — Custom Print Formats
Professional invoice/voucher templates for retreat bookings.
"""

import frappe
from frappe import _


BOOKING_CONFIRMATION_HTML = """
<style>
    .healvn-print { font-family: 'Segoe UI', sans-serif; max-width: 800px; margin: 0 auto; }
    .healvn-header { background: linear-gradient(135deg, #0f1a14, #1a2f23); color: white; padding: 30px; border-radius: 12px 12px 0 0; }
    .healvn-header h1 { margin: 0; color: #3ecf8e; font-size: 28px; }
    .healvn-header p { color: #a0c4b0; margin: 5px 0 0; }
    .healvn-body { padding: 30px; border: 1px solid #e0e0e0; }
    .healvn-section { margin-bottom: 25px; }
    .healvn-section h3 { color: #1a2f23; border-bottom: 2px solid #3ecf8e; padding-bottom: 8px; }
    .healvn-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }
    .healvn-field { padding: 8px 0; }
    .healvn-field label { display: block; font-size: 11px; color: #888; text-transform: uppercase; }
    .healvn-field .value { font-size: 15px; font-weight: 600; color: #333; }
    .healvn-total { background: #f0faf5; padding: 20px; border-radius: 8px; text-align: right; }
    .healvn-total .amount { font-size: 28px; color: #3ecf8e; font-weight: 700; }
    .healvn-footer { text-align: center; padding: 20px; color: #888; font-size: 12px; border-top: 1px solid #e0e0e0; }
    .healvn-badge { display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; }
    .badge-confirmed { background: #d4edda; color: #155724; }
    .badge-pending { background: #fff3cd; color: #856404; }
    .badge-paid { background: #cce5ff; color: #004085; }
    .healvn-trust { background: #f8f9fa; padding: 15px; border-radius: 8px; margin-top: 15px; }
    .trust-bar { height: 8px; background: #e0e0e0; border-radius: 4px; overflow: hidden; }
    .trust-fill { height: 100%; background: linear-gradient(90deg, #3ecf8e, #2da06e); border-radius: 4px; }
</style>

<div class="healvn-print">
    <div class="healvn-header">
        <h1>🌿 HealVN</h1>
        <p>Vietnam's Healing Tourism Platform</p>
        <p style="margin-top: 15px; font-size: 18px; color: white;">Booking Confirmation</p>
    </div>

    <div class="healvn-body">
        <div class="healvn-section">
            <h3>Booking Details</h3>
            <div class="healvn-grid">
                <div class="healvn-field">
                    <label>Booking ID</label>
                    <div class="value">{{ doc.booking_id }}</div>
                </div>
                <div class="healvn-field">
                    <label>Status</label>
                    <div class="value">
                        <span class="healvn-badge {% if doc.status == 'Confirmed' %}badge-confirmed{% else %}badge-pending{% endif %}">
                            {{ doc.status }}
                        </span>
                    </div>
                </div>
                <div class="healvn-field">
                    <label>Check-in</label>
                    <div class="value">{{ frappe.format_date(doc.check_in) }}</div>
                </div>
                <div class="healvn-field">
                    <label>Check-out</label>
                    <div class="value">{{ frappe.format_date(doc.check_out) }}</div>
                </div>
                <div class="healvn-field">
                    <label>Duration</label>
                    <div class="value">{{ doc.duration_nights }} nights</div>
                </div>
                <div class="healvn-field">
                    <label>Guests</label>
                    <div class="value">{{ doc.num_guests }}</div>
                </div>
            </div>
        </div>

        <div class="healvn-section">
            <h3>Guest Information</h3>
            <div class="healvn-grid">
                <div class="healvn-field">
                    <label>Name</label>
                    <div class="value">{{ doc.guest_name }}</div>
                </div>
                <div class="healvn-field">
                    <label>Email</label>
                    <div class="value">{{ doc.guest_email or '-' }}</div>
                </div>
                <div class="healvn-field">
                    <label>Phone</label>
                    <div class="value">{{ doc.guest_phone or '-' }}</div>
                </div>
                <div class="healvn-field">
                    <label>Nationality</label>
                    <div class="value">{{ doc.nationality or '-' }}</div>
                </div>
            </div>
        </div>

        <div class="healvn-section">
            <h3>Retreat</h3>
            <div class="healvn-field">
                <label>Retreat Name</label>
                <div class="value">{{ doc.retreat_name_display or doc.retreat }}</div>
            </div>
            {% if doc.special_requests %}
            <div class="healvn-field">
                <label>Special Requests</label>
                <div class="value">{{ doc.special_requests }}</div>
            </div>
            {% endif %}
        </div>

        <div class="healvn-total">
            <div>Subtotal: {{ frappe.format_currency(doc.subtotal, doc.currency) }}</div>
            {% if doc.tax_amount %}<div>Tax: {{ frappe.format_currency(doc.tax_amount, doc.currency) }}</div>{% endif %}
            {% if doc.discount_amount %}<div>Discount: -{{ frappe.format_currency(doc.discount_amount, doc.currency) }}</div>{% endif %}
            <div class="amount">{{ frappe.format_currency(doc.total_amount, doc.currency) }}</div>
            <div style="margin-top: 5px;">
                <span class="healvn-badge badge-paid">{{ doc.payment_status }}</span>
            </div>
        </div>
    </div>

    <div class="healvn-footer">
        <p>🌿 HealVN — "Chữa lành tâm hồn giữa thiên nhiên Việt"</p>
        <p>Email: hello@healvn.com | Tel: +84 123 456 789</p>
        <p>This is a computer-generated booking confirmation.</p>
    </div>
</div>
"""


def setup_print_formats():
    """Create custom print format for booking confirmations"""
    if not frappe.db.exists("Print Format", "HealVN Booking Confirmation"):
        pf = frappe.new_doc("Print Format")
        pf.name = "HealVN Booking Confirmation"
        pf.doc_type = "Retreat Booking"
        pf.module = "HealVN"
        pf.html = BOOKING_CONFIRMATION_HTML
        pf.print_format_type = "Jinja"
        pf.standard = "No"
        pf.insert(ignore_permissions=True)
