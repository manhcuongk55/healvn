# Copyright (c) 2025, HealVN Team and contributors
# For license information, please see license.txt

"""
HealVN — Custom Business Reports
Revenue analysis, occupancy rates, wellness analytics, healer performance.
These are Script Reports that appear in ERPNext's report builder.
"""

import frappe
from frappe.utils import flt, getdate, nowdate, add_days, add_months, get_first_day, get_last_day
from frappe import _


# ═══════════════════════════════════════════════════════════
# 1. RETREAT REVENUE ANALYSIS
# ═══════════════════════════════════════════════════════════

def retreat_revenue_columns():
    return [
        {"fieldname": "retreat", "label": _("Retreat"), "fieldtype": "Link", "options": "Retreat", "width": 200},
        {"fieldname": "location", "label": _("Location"), "fieldtype": "Data", "width": 150},
        {"fieldname": "category", "label": _("Category"), "fieldtype": "Data", "width": 120},
        {"fieldname": "total_bookings", "label": _("Bookings"), "fieldtype": "Int", "width": 90},
        {"fieldname": "completed_bookings", "label": _("Completed"), "fieldtype": "Int", "width": 90},
        {"fieldname": "cancelled_bookings", "label": _("Cancelled"), "fieldtype": "Int", "width": 90},
        {"fieldname": "total_guests", "label": _("Guests"), "fieldtype": "Int", "width": 80},
        {"fieldname": "gross_revenue", "label": _("Gross Revenue"), "fieldtype": "Currency", "width": 130},
        {"fieldname": "commission", "label": _("Commission (15%)"), "fieldtype": "Currency", "width": 130},
        {"fieldname": "avg_booking_value", "label": _("Avg Booking"), "fieldtype": "Currency", "width": 120},
        {"fieldname": "avg_rating", "label": _("Rating"), "fieldtype": "Float", "precision": 1, "width": 80},
        {"fieldname": "verification_score", "label": _("Trust %"), "fieldtype": "Percent", "width": 80},
        {"fieldname": "cancellation_rate", "label": _("Cancel %"), "fieldtype": "Percent", "width": 80},
    ]


def retreat_revenue_data(filters):
    from_date = filters.get("from_date") or str(get_first_day(add_months(nowdate(), -3)))
    to_date = filters.get("to_date") or nowdate()

    data = frappe.db.sql("""
        SELECT
            b.retreat,
            r.retreat_name,
            r.location,
            r.category,
            COUNT(*) as total_bookings,
            COUNT(CASE WHEN b.status = 'Completed' THEN 1 END) as completed_bookings,
            COUNT(CASE WHEN b.status = 'Cancelled' THEN 1 END) as cancelled_bookings,
            COALESCE(SUM(b.num_guests), 0) as total_guests,
            COALESCE(SUM(CASE WHEN b.status IN ('Confirmed','Completed') THEN b.total_amount END), 0) as gross_revenue,
            COALESCE(AVG(CASE WHEN b.status IN ('Confirmed','Completed') THEN b.total_amount END), 0) as avg_booking_value,
            r.average_rating as avg_rating,
            r.verification_score
        FROM `tabRetreat Booking` b
        JOIN `tabRetreat` r ON b.retreat = r.name
        WHERE b.creation BETWEEN %(from_date)s AND %(to_date)s
        GROUP BY b.retreat
        ORDER BY gross_revenue DESC
    """, {"from_date": from_date, "to_date": to_date}, as_dict=True)

    for row in data:
        row["commission"] = flt(row["gross_revenue"] * 0.15, 2)
        row["cancellation_rate"] = (
            flt(row["cancelled_bookings"] / row["total_bookings"] * 100, 1)
            if row["total_bookings"] else 0
        )

    return data


# ═══════════════════════════════════════════════════════════
# 2. OCCUPANCY REPORT
# ═══════════════════════════════════════════════════════════

def occupancy_columns():
    return [
        {"fieldname": "retreat", "label": _("Retreat"), "fieldtype": "Link", "options": "Retreat", "width": 200},
        {"fieldname": "max_guests", "label": _("Capacity"), "fieldtype": "Int", "width": 80},
        {"fieldname": "days_analyzed", "label": _("Days"), "fieldtype": "Int", "width": 70},
        {"fieldname": "total_guest_nights", "label": _("Guest-Nights"), "fieldtype": "Int", "width": 110},
        {"fieldname": "total_capacity_nights", "label": _("Capacity-Nights"), "fieldtype": "Int", "width": 130},
        {"fieldname": "occupancy_rate", "label": _("Occupancy %"), "fieldtype": "Percent", "width": 100},
        {"fieldname": "peak_occupancy", "label": _("Peak Occ %"), "fieldtype": "Percent", "width": 100},
        {"fieldname": "avg_stay_nights", "label": _("Avg Stay"), "fieldtype": "Float", "precision": 1, "width": 90},
        {"fieldname": "revenue_per_night", "label": _("Rev/Night"), "fieldtype": "Currency", "width": 110},
    ]


def occupancy_data(filters):
    from_date = getdate(filters.get("from_date") or get_first_day(nowdate()))
    to_date = getdate(filters.get("to_date") or nowdate())
    days = (to_date - from_date).days or 1

    retreats = frappe.get_all(
        "Retreat",
        filters={"status": "Active"},
        fields=["name", "retreat_name", "max_guests"],
    )

    data = []
    for retreat in retreats:
        bookings = frappe.db.sql("""
            SELECT
                COUNT(*) as count,
                COALESCE(SUM(duration_nights), 0) as total_nights,
                COALESCE(SUM(num_guests * duration_nights), 0) as guest_nights,
                COALESCE(AVG(duration_nights), 0) as avg_stay,
                COALESCE(SUM(total_amount), 0) as total_revenue
            FROM `tabRetreat Booking`
            WHERE retreat = %s
              AND status IN ('Confirmed', 'Completed', 'Checked In')
              AND check_in <= %s AND check_out >= %s
        """, (retreat.name, str(to_date), str(from_date)), as_dict=True)[0]

        capacity_nights = (retreat.max_guests or 1) * days
        occupancy = flt(bookings.guest_nights / capacity_nights * 100, 1) if capacity_nights else 0

        data.append({
            "retreat": retreat.name,
            "max_guests": retreat.max_guests,
            "days_analyzed": days,
            "total_guest_nights": bookings.guest_nights,
            "total_capacity_nights": capacity_nights,
            "occupancy_rate": min(100, occupancy),
            "peak_occupancy": min(100, occupancy * 1.3),  # estimate
            "avg_stay_nights": flt(bookings.avg_stay, 1),
            "revenue_per_night": flt(bookings.total_revenue / days, 2) if days else 0,
        })

    data.sort(key=lambda x: x["occupancy_rate"], reverse=True)
    return data


# ═══════════════════════════════════════════════════════════
# 3. WELLNESS ANALYTICS
# ═══════════════════════════════════════════════════════════

def wellness_columns():
    return [
        {"fieldname": "metric", "label": _("Metric"), "fieldtype": "Data", "width": 250},
        {"fieldname": "value", "label": _("Value"), "fieldtype": "Data", "width": 150},
        {"fieldname": "change", "label": _("Change"), "fieldtype": "Data", "width": 100},
        {"fieldname": "trend", "label": _("Trend"), "fieldtype": "Data", "width": 80},
    ]


def wellness_data(filters):
    from_date = filters.get("from_date") or str(get_first_day(add_months(nowdate(), -1)))
    to_date = filters.get("to_date") or nowdate()

    # Previous period for comparison
    period_days = (getdate(to_date) - getdate(from_date)).days
    prev_from = str(getdate(from_date) - frappe.utils.datetime.timedelta(days=period_days))
    prev_to = str(getdate(from_date) - frappe.utils.datetime.timedelta(days=1))

    def get_count(doctype, status_filter=None, date_field="creation", period="current"):
        f = {date_field: ["between", [from_date, to_date] if period == "current" else [prev_from, prev_to]]}
        if status_filter:
            f.update(status_filter)
        return frappe.db.count(doctype, f) or 0

    def get_sum(doctype, field, status_filter=None, period="current"):
        ff = [from_date, to_date] if period == "current" else [prev_from, prev_to]
        conds = f"creation BETWEEN '{ff[0]}' AND '{ff[1]}'"
        if status_filter:
            for k, v in status_filter.items():
                conds += f" AND {k} = '{v}'"
        return flt(frappe.db.sql(
            f"SELECT COALESCE(SUM({field}), 0) FROM `tab{doctype}` WHERE {conds}"
        )[0][0])

    def trend(curr, prev):
        if prev == 0:
            return "🆕" if curr > 0 else "—"
        change = flt((curr - prev) / prev * 100, 1)
        return f"{'📈' if change > 0 else '📉'} {'+' if change > 0 else ''}{change}%"

    # Metrics
    bookings_curr = get_count("Retreat Booking")
    bookings_prev = get_count("Retreat Booking", period="prev")

    revenue_curr = get_sum("Retreat Booking", "total_amount", {"status": "Completed"})
    revenue_prev = get_sum("Retreat Booking", "total_amount", {"status": "Completed"}, "prev")

    leads_curr = get_count("Retreat Lead")
    leads_prev = get_count("Retreat Lead", period="prev")

    converted = get_count("Retreat Lead", {"status": "Converted"})
    conv_prev = get_count("Retreat Lead", {"status": "Converted"}, period="prev")

    guests_curr = get_sum("Retreat Booking", "num_guests")
    guests_prev = get_sum("Retreat Booking", "num_guests", period="prev")

    active_retreats = frappe.db.count("Retreat", {"status": "Active"})
    active_healers = frappe.db.count("Healer", {"status": "Active"})
    avg_rating = flt(frappe.db.sql(
        "SELECT AVG(average_rating) FROM `tabRetreat` WHERE status='Active'"
    )[0][0] or 0, 1)

    data = [
        {"metric": "📊 Total Bookings", "value": str(bookings_curr), "change": str(bookings_curr - bookings_prev), "trend": trend(bookings_curr, bookings_prev)},
        {"metric": "💰 Gross Revenue", "value": f"${revenue_curr:,.0f}", "change": f"${revenue_curr - revenue_prev:,.0f}", "trend": trend(revenue_curr, revenue_prev)},
        {"metric": "💵 Platform Commission (15%)", "value": f"${revenue_curr * 0.15:,.0f}", "change": "", "trend": ""},
        {"metric": "👥 Total Guests", "value": str(int(guests_curr)), "change": str(int(guests_curr - guests_prev)), "trend": trend(guests_curr, guests_prev)},
        {"metric": "📥 New Leads", "value": str(leads_curr), "change": str(leads_curr - leads_prev), "trend": trend(leads_curr, leads_prev)},
        {"metric": "✅ Converted Leads", "value": str(converted), "change": str(converted - conv_prev), "trend": trend(converted, conv_prev)},
        {"metric": "📈 Conversion Rate", "value": f"{flt(converted / leads_curr * 100, 1) if leads_curr else 0}%", "change": "", "trend": ""},
        {"metric": "🏨 Active Retreats", "value": str(active_retreats), "change": "", "trend": ""},
        {"metric": "🧘 Active Healers", "value": str(active_healers), "change": "", "trend": ""},
        {"metric": "⭐ Avg Retreat Rating", "value": str(avg_rating), "change": "", "trend": ""},
        {"metric": "💰 Avg Booking Value", "value": f"${flt(revenue_curr / bookings_curr, 0):,.0f}" if bookings_curr else "$0", "change": "", "trend": ""},
    ]

    return data


# ═══════════════════════════════════════════════════════════
# 4. HEALER PERFORMANCE REPORT
# ═══════════════════════════════════════════════════════════

@frappe.whitelist()
def get_healer_performance(from_date=None, to_date=None):
    """API for healer performance dashboard"""
    frappe.only_for(["System Manager", "Retreat Manager"])

    from_date = from_date or str(get_first_day(add_months(nowdate(), -1)))
    to_date = to_date or nowdate()

    healers = frappe.get_all(
        "Healer",
        filters={"status": "Active"},
        fields=["name", "healer_name", "specialty", "session_rate",
                "average_rating", "total_reviews", "trust_verified"],
    )

    for healer in healers:
        # Get earnings from retreat expenses
        earnings = frappe.db.sql("""
            SELECT COALESCE(SUM(amount), 0)
            FROM `tabRetreat Expense`
            WHERE healer = %s AND expense_type = 'Healer Payment'
              AND expense_date BETWEEN %s AND %s AND docstatus = 1
        """, (healer.name, from_date, to_date))[0][0]
        healer["total_earnings"] = flt(earnings, 2)

    healers.sort(key=lambda x: x["total_earnings"], reverse=True)
    return {"status": "success", "data": healers}


# ═══════════════════════════════════════════════════════════
# 5. COMPREHENSIVE BUSINESS DASHBOARD API
# ═══════════════════════════════════════════════════════════

@frappe.whitelist()
def get_business_dashboard():
    """
    Master dashboard with ALL business metrics.
    Used by the admin panel for full operational visibility.
    """
    frappe.only_for(["System Manager", "Retreat Manager"])

    today = nowdate()
    month_start = str(get_first_day(today))
    last_month_start = str(get_first_day(add_months(today, -1)))
    last_month_end = str(get_last_day(add_months(today, -1)))

    # ─── Revenue Metrics ──────────────────────────
    this_month_revenue = flt(frappe.db.sql(
        "SELECT COALESCE(SUM(total_amount), 0) FROM `tabRetreat Booking` "
        "WHERE status IN ('Confirmed','Completed') AND creation >= %s",
        month_start
    )[0][0])

    last_month_revenue = flt(frappe.db.sql(
        "SELECT COALESCE(SUM(total_amount), 0) FROM `tabRetreat Booking` "
        "WHERE status IN ('Confirmed','Completed') AND creation BETWEEN %s AND %s",
        (last_month_start, last_month_end)
    )[0][0])

    # ─── Booking Metrics ──────────────────────────
    bookings_today = frappe.db.count("Retreat Booking", {"creation": [">=", today]})
    bookings_month = frappe.db.count("Retreat Booking", {"creation": [">=", month_start]})
    pending_bookings = frappe.db.count("Retreat Booking", {"status": "Pending"})
    checkins_today = frappe.db.count("Retreat Booking", {"check_in": today, "status": "Confirmed"})

    # ─── Lead Metrics ─────────────────────────────
    new_leads_today = frappe.db.count("Retreat Lead", {"creation": [">=", today], "status": "New"})
    hot_leads = frappe.db.count("Retreat Lead", {"priority": "Hot", "status": ["not in", ["Converted", "Lost"]]})

    # ─── Expense Metrics ──────────────────────────
    month_expenses = flt(frappe.db.sql(
        "SELECT COALESCE(SUM(amount), 0) FROM `tabRetreat Expense` "
        "WHERE docstatus=1 AND expense_date >= %s", month_start
    )[0][0])

    # ─── Inventory / Capacity ─────────────────────
    total_retreats = frappe.db.count("Retreat", {"status": "Active"})
    total_healers = frappe.db.count("Healer", {"status": "Active"})
    total_packages = frappe.db.count("Retreat Package", {"status": "Active"}) if frappe.db.table_exists("tabRetreat Package") else 0

    # ─── Monthly Trend (12 months) ────────────────
    monthly_trend = frappe.db.sql("""
        SELECT
            DATE_FORMAT(creation, '%%Y-%%m') as month,
            COUNT(*) as bookings,
            COALESCE(SUM(total_amount), 0) as revenue,
            COALESCE(SUM(num_guests), 0) as guests
        FROM `tabRetreat Booking`
        WHERE creation >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH)
          AND status IN ('Confirmed', 'Completed')
        GROUP BY DATE_FORMAT(creation, '%%Y-%%m')
        ORDER BY month
    """, as_dict=True)

    # ─── Top Revenue Sources ──────────────────────
    top_retreats = frappe.db.sql("""
        SELECT retreat, COUNT(*) as bookings, SUM(total_amount) as revenue
        FROM `tabRetreat Booking`
        WHERE status IN ('Confirmed','Completed') AND creation >= %s
        GROUP BY retreat ORDER BY revenue DESC LIMIT 5
    """, month_start, as_dict=True)

    # ─── Lead Sources ────────────────────────────
    lead_sources = frappe.db.sql("""
        SELECT source, COUNT(*) as count
        FROM `tabRetreat Lead`
        WHERE creation >= %s
        GROUP BY source ORDER BY count DESC
    """, month_start, as_dict=True)

    return {
        "status": "success",
        "data": {
            "revenue": {
                "this_month": this_month_revenue,
                "last_month": last_month_revenue,
                "growth_pct": flt((this_month_revenue - last_month_revenue) / last_month_revenue * 100, 1) if last_month_revenue else 0,
                "commission": flt(this_month_revenue * 0.15, 2),
            },
            "bookings": {
                "today": bookings_today,
                "this_month": bookings_month,
                "pending": pending_bookings,
                "checkins_today": checkins_today,
            },
            "leads": {
                "new_today": new_leads_today,
                "hot": hot_leads,
            },
            "expenses": {
                "this_month": month_expenses,
                "net_profit": flt(this_month_revenue * 0.15 - month_expenses, 2),
            },
            "inventory": {
                "retreats": total_retreats,
                "healers": total_healers,
                "packages": total_packages,
            },
            "trends": {
                "monthly": monthly_trend,
                "top_retreats": top_retreats,
                "lead_sources": lead_sources,
            },
        },
    }
