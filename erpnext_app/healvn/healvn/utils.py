# Copyright (c) 2025, HealVN Team and contributors
# For license information, please see license.txt

"""
HealVN — Utility functions
"""

import frappe
from frappe.utils import flt, fmt_money
from frappe import _


def format_currency_vnd(amount, currency="VND"):
    """Format currency for Vietnamese display"""
    if currency == "VND":
        return f"{flt(amount):,.0f}₫"
    elif currency == "USD":
        return f"${flt(amount):,.2f}"
    return fmt_money(amount, currency=currency)


def get_retreat_thumbnail(retreat_name):
    """Get thumbnail URL for a retreat"""
    return frappe.db.get_value("Retreat", retreat_name, "thumbnail") or ""


def notify_booking_payment(doc, method):
    """Called when Sales Invoice is submitted — update booking payment status"""
    # Find booking linked through Sales Order
    if doc.items:
        for item in doc.items:
            if item.sales_order:
                booking = frappe.db.get_value(
                    "Retreat Booking",
                    {"sales_order": item.sales_order},
                    "name",
                )
                if booking:
                    frappe.db.set_value("Retreat Booking", booking, {
                        "payment_status": "Paid",
                        "sales_invoice": doc.name,
                    })
                    frappe.msgprint(
                        _("Booking {0} payment status updated to Paid").format(booking),
                        alert=True,
                    )


def get_retreat_stats(retreat_name):
    """Get comprehensive stats for a retreat"""
    bookings = frappe.db.sql("""
        SELECT
            COUNT(*) as total_bookings,
            COUNT(CASE WHEN status = 'Completed' THEN 1 END) as completed,
            COUNT(CASE WHEN status = 'Cancelled' THEN 1 END) as cancelled,
            COALESCE(SUM(CASE WHEN status IN ('Confirmed','Completed') THEN total_amount END), 0) as revenue,
            COALESCE(AVG(CASE WHEN status = 'Completed' THEN num_guests END), 0) as avg_guests
        FROM `tabRetreat Booking`
        WHERE retreat = %s
    """, retreat_name, as_dict=True)[0]

    return bookings


def calculate_commission(amount, rate=0.15):
    """Calculate platform commission"""
    return flt(amount * rate, 2)
