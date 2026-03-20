# Copyright (c) 2025, HealVN Team and contributors
# For license information, please see license.txt

"""
HealVN — Scheduled Tasks
Run via Frappe scheduler (defined in hooks.py)
"""

import frappe
from frappe.utils import nowdate, add_days, getdate, flt
from frappe import _


# ─── Daily Tasks ──────────────────────────────────────────

def send_checkin_reminders():
    """Send email reminders to guests checking in tomorrow"""
    tomorrow = add_days(nowdate(), 1)
    bookings = frappe.get_all(
        "Retreat Booking",
        filters={
            "check_in": tomorrow,
            "status": "Confirmed",
        },
        fields=["name", "guest_name", "guest_email", "retreat", "check_in", "check_out"],
    )

    for booking in bookings:
        if not booking.guest_email:
            continue
        retreat_name = frappe.db.get_value("Retreat", booking.retreat, "retreat_name")
        frappe.sendmail(
            recipients=[booking.guest_email],
            subject=f"🌿 Reminder: Check-in tomorrow at {retreat_name}",
            message=f"""
                <h2>Xin chào {booking.guest_name}!</h2>
                <p>Nhắc bạn: ngày mai là ngày check-in tại <strong>{retreat_name}</strong>.</p>
                <p>Check-in: {booking.check_in}<br/>
                Check-out: {booking.check_out}</p>
                <p>Chúc bạn một hành trình chữa lành tuyệt vời! 🌿</p>
                <p>— HealVN Team</p>
            """,
        )

    frappe.log("HealVN: Sent {0} check-in reminders".format(len(bookings)))


def update_retreat_ratings():
    """Recalculate average ratings for all active retreats"""
    retreats = frappe.get_all("Retreat", filters={"status": "Active"}, pluck="name")

    for retreat_name in retreats:
        retreat = frappe.get_doc("Retreat", retreat_name)
        retreat.calculate_average_rating()
        retreat.db_set("average_rating", retreat.average_rating, update_modified=False)
        retreat.db_set("total_reviews", retreat.total_reviews, update_modified=False)


def expire_pending_bookings():
    """Auto-cancel bookings pending for more than 48 hours"""
    cutoff = add_days(nowdate(), -2)

    expired = frappe.get_all(
        "Retreat Booking",
        filters={
            "status": "Pending",
            "creation": ["<", cutoff],
        },
        pluck="name",
    )

    for booking_name in expired:
        booking = frappe.get_doc("Retreat Booking", booking_name)
        booking.status = "Cancelled"
        booking.internal_notes = "Auto-cancelled: pending for >48 hours"
        booking.save(ignore_permissions=True)

    if expired:
        frappe.log(f"HealVN: Auto-cancelled {len(expired)} expired bookings")


# ─── Weekly Tasks ─────────────────────────────────────────

def generate_wellness_reports():
    """Generate weekly wellness analytics for retreat partners"""
    retreats = frappe.get_all(
        "Retreat",
        filters={"status": "Active"},
        fields=["name", "retreat_name", "retreat_owner", "contact_email"],
    )

    for retreat in retreats:
        if not retreat.contact_email:
            continue

        # Get weekly stats
        week_ago = add_days(nowdate(), -7)
        bookings = frappe.db.count("Retreat Booking", {
            "retreat": retreat.name,
            "creation": [">=", week_ago],
        })
        revenue = frappe.db.sql(
            "SELECT COALESCE(SUM(total_amount), 0) FROM `tabRetreat Booking` "
            "WHERE retreat=%s AND creation >= %s AND status != 'Cancelled'",
            (retreat.name, week_ago),
        )[0][0]

        if bookings > 0:
            frappe.sendmail(
                recipients=[retreat.contact_email],
                subject=f"📊 Weekly Report — {retreat.retreat_name}",
                message=f"""
                    <h2>Weekly Performance Report</h2>
                    <p><strong>{retreat.retreat_name}</strong></p>
                    <table>
                        <tr><td>New Bookings</td><td><strong>{bookings}</strong></td></tr>
                        <tr><td>Revenue</td><td><strong>${flt(revenue, 2):,.2f}</strong></td></tr>
                    </table>
                    <p>— HealVN Platform</p>
                """,
            )


def sync_retreat_availability():
    """Sync availability data for retreats with external calendars"""
    # Placeholder for iCal / Google Calendar sync
    retreats = frappe.get_all(
        "Retreat",
        filters={"status": "Active", "ical_url": ["is", "set"]},
        fields=["name", "ical_url"],
    )
    for retreat in retreats:
        try:
            # Future: parse iCal and update blocked dates
            pass
        except Exception as e:
            frappe.log_error(f"iCal sync error for {retreat.name}: {str(e)}")


# ─── Monthly Tasks ────────────────────────────────────────

def send_partner_reports():
    """Send monthly partner revenue reports with commission details"""
    from frappe.utils import get_first_day, get_last_day, add_months

    last_month_start = get_first_day(add_months(nowdate(), -1))
    last_month_end = get_last_day(add_months(nowdate(), -1))

    retreats = frappe.get_all(
        "Retreat",
        filters={"status": "Active"},
        fields=["name", "retreat_name", "contact_email"],
    )

    for retreat in retreats:
        if not retreat.contact_email:
            continue

        stats = frappe.db.sql("""
            SELECT
                COUNT(*) as total_bookings,
                COALESCE(SUM(total_amount), 0) as total_revenue,
                COALESCE(AVG(total_amount), 0) as avg_booking_value,
                COUNT(CASE WHEN status = 'Completed' THEN 1 END) as completed,
                COUNT(CASE WHEN status = 'Cancelled' THEN 1 END) as cancelled
            FROM `tabRetreat Booking`
            WHERE retreat = %s
              AND creation BETWEEN %s AND %s
        """, (retreat.name, last_month_start, last_month_end), as_dict=True)[0]

        if stats.total_bookings > 0:
            commission = flt(stats.total_revenue * 0.15, 2)  # 15% commission
            net_revenue = flt(stats.total_revenue - commission, 2)

            frappe.sendmail(
                recipients=[retreat.contact_email],
                subject=f"📊 Monthly Report — {retreat.retreat_name}",
                message=f"""
                    <h2>Monthly Partner Report</h2>
                    <p>Period: {last_month_start} to {last_month_end}</p>
                    <table>
                        <tr><td>Total Bookings</td><td>{stats.total_bookings}</td></tr>
                        <tr><td>Gross Revenue</td><td>${stats.total_revenue:,.2f}</td></tr>
                        <tr><td>Platform Commission (15%)</td><td>${commission:,.2f}</td></tr>
                        <tr><td><strong>Net Revenue</strong></td><td><strong>${net_revenue:,.2f}</strong></td></tr>
                        <tr><td>Completed</td><td>{stats.completed}</td></tr>
                        <tr><td>Cancelled</td><td>{stats.cancelled}</td></tr>
                    </table>
                """,
            )
