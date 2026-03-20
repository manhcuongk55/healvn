# Copyright (c) 2025, HealVN Team and contributors
# For license information, please see license.txt

"""
HealVN REST API Layer
Public endpoints consumed by the frontend application.
All methods are whitelisted for external access.
"""

import frappe
from frappe import _
from frappe.utils import flt, nowdate, getdate, cint
import json


# ═══════════════════════════════════════════════════════════
# RETREATS API
# ═══════════════════════════════════════════════════════════

@frappe.whitelist(allow_guest=True)
def get_retreats(
    category=None,
    province=None,
    min_price=None,
    max_price=None,
    wellness_type=None,
    search=None,
    sort_by="average_rating",
    sort_order="desc",
    page=1,
    page_size=12,
):
    """
    Get retreat listings for marketplace.
    Returns paginated, filtered, and sorted retreat list.

    Args:
        category: Filter by retreat category
        province: Filter by province/territory
        min_price/max_price: Price range filter
        wellness_type: Filter by wellness type (yoga, spa, detox, etc)
        search: Full-text search on name, location, description
        sort_by: Sort field (average_rating, price_per_night, verification_score)
        sort_order: asc or desc
        page: Page number (1-indexed)
        page_size: Results per page (max 50)
    """
    filters = {"status": "Active"}

    if category:
        filters["category"] = category
    if province:
        filters["province"] = province

    # Build conditions for price range
    conditions = []
    if min_price:
        conditions.append(f"price_per_night >= {flt(min_price)}")
    if max_price:
        conditions.append(f"price_per_night <= {flt(max_price)}")

    # Search
    if search:
        conditions.append(
            f"(retreat_name LIKE '%{frappe.db.escape(search)}%' "
            f"OR location LIKE '%{frappe.db.escape(search)}%' "
            f"OR description LIKE '%{frappe.db.escape(search)}%')"
        )

    # Validate sort
    valid_sorts = ["average_rating", "price_per_night", "verification_score", "creation"]
    if sort_by not in valid_sorts:
        sort_by = "average_rating"
    if sort_order not in ("asc", "desc"):
        sort_order = "desc"

    page = max(1, cint(page))
    page_size = min(50, max(1, cint(page_size)))

    retreats = frappe.get_all(
        "Retreat",
        filters=filters,
        fields=[
            "name", "retreat_name", "location", "province", "category",
            "price_per_night", "price_per_package", "package_duration_days",
            "currency", "average_rating", "total_reviews",
            "verification_status", "verification_score", "thumbnail",
            "max_guests", "latitude", "longitude",
        ],
        or_filters=None,
        order_by=f"{sort_by} {sort_order}",
        limit_start=(page - 1) * page_size,
        limit_page_length=page_size,
    )

    total = frappe.db.count("Retreat", filters=filters)

    return {
        "status": "success",
        "data": retreats,
        "pagination": {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": -(-total // page_size),  # ceil division
        },
    }


@frappe.whitelist(allow_guest=True)
def get_retreat_detail(retreat_name):
    """Get full retreat details including reviews, healers, availability"""
    if not frappe.db.exists("Retreat", retreat_name):
        frappe.throw(_("Retreat not found"), frappe.DoesNotExistError)

    retreat = frappe.get_doc("Retreat", retreat_name)
    data = retreat.as_marketplace_dict()

    # Add linked healers
    healer_links = frappe.get_all(
        "Healer Retreat Link",
        filters={"retreat": retreat_name},
        fields=["parent"],
    )
    if healer_links:
        healers = []
        for hl in healer_links:
            healer = frappe.get_doc("Healer", hl.parent)
            healers.append(healer.as_profile_dict())
        data["healers"] = healers
    else:
        data["healers"] = []

    # 30-day availability preview
    availability = []
    for i in range(30):
        date = str(getdate(nowdate()) + frappe.utils.datetime.timedelta(days=i))
        avail = retreat.check_availability(date, str(getdate(date) + frappe.utils.datetime.timedelta(days=1)))
        availability.append({
            "date": date,
            "available": avail["available"],
            "slots": avail["slots_remaining"],
        })
    data["availability_30d"] = availability

    return {"status": "success", "data": data}


@frappe.whitelist(allow_guest=True)
def check_availability(retreat_name, check_in, check_out):
    """Check retreat availability for specific dates"""
    retreat = frappe.get_doc("Retreat", retreat_name)
    result = retreat.check_availability(check_in, check_out)
    return {"status": "success", "data": result}


# ═══════════════════════════════════════════════════════════
# BOOKING API
# ═══════════════════════════════════════════════════════════

@frappe.whitelist()
def create_booking(
    retreat,
    guest_name,
    guest_email,
    check_in,
    check_out,
    num_guests=1,
    guest_phone=None,
    nationality=None,
    special_requests=None,
):
    """
    Create a new retreat booking.
    Requires authenticated user.
    """
    # Validate retreat exists and is active
    retreat_doc = frappe.get_doc("Retreat", retreat)
    if retreat_doc.status != "Active":
        frappe.throw(_("This retreat is not currently accepting bookings"))

    # Check availability
    avail = retreat_doc.check_availability(check_in, check_out)
    if not avail["available"]:
        frappe.throw(_("No availability for the selected dates"))

    # Create booking
    booking = frappe.new_doc("Retreat Booking")
    booking.retreat = retreat
    booking.guest_name = guest_name
    booking.guest_email = guest_email
    booking.guest_phone = guest_phone
    booking.check_in = check_in
    booking.check_out = check_out
    booking.num_guests = cint(num_guests)
    booking.nationality = nationality
    booking.special_requests = special_requests
    booking.status = "Pending"
    booking.insert(ignore_permissions=True)

    return {
        "status": "success",
        "message": _("Booking created successfully"),
        "data": booking.as_booking_dict(),
    }


@frappe.whitelist()
def get_my_bookings(status=None, page=1, page_size=10):
    """Get bookings for the logged-in user"""
    user = frappe.session.user
    if user == "Guest":
        frappe.throw(_("Please login to view your bookings"))

    # Find customer linked to user
    customer = frappe.db.get_value("Customer", {"email_id": user})

    filters = {}
    if customer:
        filters["customer"] = customer
    else:
        filters["guest_email"] = user

    if status:
        filters["status"] = status

    bookings = frappe.get_all(
        "Retreat Booking",
        filters=filters,
        fields=[
            "name", "booking_id", "retreat", "guest_name",
            "check_in", "check_out", "num_guests", "total_amount",
            "status", "payment_status", "creation",
        ],
        order_by="creation desc",
        limit_start=(cint(page) - 1) * cint(page_size),
        limit_page_length=cint(page_size),
    )

    # Enrich with retreat names
    for b in bookings:
        b["retreat_name"] = frappe.db.get_value("Retreat", b["retreat"], "retreat_name")

    return {"status": "success", "data": bookings}


@frappe.whitelist()
def confirm_booking(booking_name):
    """Confirm a pending booking (manager action)"""
    booking = frappe.get_doc("Retreat Booking", booking_name)
    if booking.status != "Pending":
        frappe.throw(_("Only pending bookings can be confirmed"))
    booking.status = "Confirmed"
    booking.save()
    return {"status": "success", "message": _("Booking confirmed")}


@frappe.whitelist()
def cancel_booking(booking_name, reason=None):
    """Cancel a booking"""
    booking = frappe.get_doc("Retreat Booking", booking_name)
    if booking.status in ("Completed", "Cancelled"):
        frappe.throw(_("Cannot cancel a completed or already cancelled booking"))
    booking.status = "Cancelled"
    if reason:
        booking.internal_notes = f"Cancellation reason: {reason}"
    booking.save()
    return {"status": "success", "message": _("Booking cancelled")}


# ═══════════════════════════════════════════════════════════
# AI RECOMMENDATION API
# ═══════════════════════════════════════════════════════════

@frappe.whitelist(allow_guest=True)
def ai_recommend(
    stress_level=None,
    budget=None,
    duration_days=None,
    preferences=None,
    province=None,
):
    """
    AI-powered retreat recommendation.
    Analyzes inputs and returns top retreat matches with match scores.
    """
    # Parse preferences
    if preferences and isinstance(preferences, str):
        try:
            preferences = json.loads(preferences)
        except json.JSONDecodeError:
            preferences = [preferences]

    # Get all active, verified retreats
    retreats = frappe.get_all(
        "Retreat",
        filters={
            "status": "Active",
            "verification_status": ["in", ["Fully Verified", "Partially Verified"]],
        },
        fields=[
            "name", "retreat_name", "location", "province", "category",
            "price_per_night", "price_per_package", "package_duration_days",
            "average_rating", "verification_score", "thumbnail",
            "currency",
        ],
    )

    # Score & rank retreats
    scored_retreats = []
    for r in retreats:
        score = calculate_match_score(r, budget, duration_days, preferences, province, stress_level)
        r["match_score"] = score
        scored_retreats.append(r)

    # Sort by match score
    scored_retreats.sort(key=lambda x: x["match_score"], reverse=True)

    # Return top 5
    top = scored_retreats[:5]

    # Generate AI commentary
    commentary = generate_recommendation_text(top, stress_level, preferences)

    return {
        "status": "success",
        "data": {
            "recommendations": top,
            "commentary": commentary,
            "total_analyzed": len(retreats),
        },
    }


def calculate_match_score(retreat, budget, duration_days, preferences, province, stress_level):
    """Calculate a match score (0–100) for a retreat based on user criteria"""
    score = 50  # baseline

    # Rating bonus: max +20
    score += flt(retreat.get("average_rating", 0)) * 4

    # Verification bonus: max +15
    score += flt(retreat.get("verification_score", 0)) * 0.15

    # Budget fit: +15 if within budget, -10 if over
    if budget:
        budget = flt(budget)
        estimated_cost = (
            flt(retreat.get("price_per_package"))
            or flt(retreat.get("price_per_night", 0)) * flt(duration_days or 5)
        )
        if estimated_cost <= budget:
            score += 15
        elif estimated_cost <= budget * 1.2:
            score += 5
        else:
            score -= 10

    # Province match: +10
    if province and retreat.get("province") == province:
        score += 10

    # Stress-based: higher stress → prefer luxury/spa categories
    if stress_level:
        stress = flt(stress_level)
        if stress > 7 and retreat.get("category") in ("Luxury", "Spa & Wellness"):
            score += 10
        elif stress > 5 and retreat.get("category") in ("Yoga & Meditation", "Eco Retreat"):
            score += 8

    # Cap score at 100
    return min(100, max(0, round(score)))


def generate_recommendation_text(retreats, stress_level, preferences):
    """Generate human-readable recommendation text"""
    if not retreats:
        return "Chưa tìm thấy retreat phù hợp. Hãy thử mở rộng tiêu chí tìm kiếm!"

    top = retreats[0]
    lines = [
        f"🌿 **Gợi ý hàng đầu: {top['retreat_name']}** (Match: {top['match_score']}%)",
        f"📍 {top['location']}, {top.get('province', 'Vietnam')}",
        f"⭐ Rating: {top.get('average_rating', 'N/A')}",
    ]

    if stress_level and flt(stress_level) > 7:
        lines.append("\n💆 Mức stress của bạn khá cao — mình đề xuất retreat có spa và therapist chuyên nghiệp.")

    if len(retreats) > 1:
        lines.append(f"\n📋 Mình đã phân tích {len(retreats)} retreat phù hợp. Bấm vào để xem chi tiết!")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════
# WELLNESS JOURNEY API
# ═══════════════════════════════════════════════════════════

@frappe.whitelist()
def create_wellness_journey(
    guest_name,
    start_date,
    duration_days=5,
    budget=None,
    stress_level=None,
    physical_score=None,
    mental_score=None,
    preferences=None,
    preferred_province=None,
):
    """Create and auto-generate an AI wellness journey"""
    from frappe.utils import add_days, getdate

    journey = frappe.new_doc("Wellness Journey")
    journey.guest_name = guest_name
    journey.start_date = start_date
    journey.end_date = str(add_days(getdate(start_date), cint(duration_days)))
    journey.duration_days = cint(duration_days)
    journey.budget = flt(budget)
    journey.stress_level = flt(stress_level)
    journey.physical_score = flt(physical_score)
    journey.mental_score = flt(mental_score)
    journey.preferred_province = preferred_province
    journey.status = "Draft"

    journey.insert(ignore_permissions=True)

    # Auto-generate AI itinerary
    result = journey.generate_ai_journey()

    return {
        "status": "success",
        "data": journey.as_journey_dict(),
    }


@frappe.whitelist()
def get_wellness_journey(journey_name):
    """Get a wellness journey with full itinerary"""
    journey = frappe.get_doc("Wellness Journey", journey_name)
    return {"status": "success", "data": journey.as_journey_dict()}


# ═══════════════════════════════════════════════════════════
# HEALERS API
# ═══════════════════════════════════════════════════════════

@frappe.whitelist(allow_guest=True)
def get_healers(specialty=None, province=None, retreat=None, page=1, page_size=12):
    """Get healer listings"""
    filters = {"status": "Active"}
    if specialty:
        filters["specialty"] = specialty
    if province:
        filters["province"] = province

    healers = frappe.get_all(
        "Healer",
        filters=filters,
        fields=[
            "name", "healer_name", "specialty", "bio",
            "session_rate", "daily_rate", "currency",
            "average_rating", "total_reviews", "trust_verified",
            "photo", "province", "experience_years",
        ],
        order_by="average_rating desc",
        limit_start=(cint(page) - 1) * cint(page_size),
        limit_page_length=cint(page_size),
    )

    return {"status": "success", "data": healers}


# ═══════════════════════════════════════════════════════════
# ANALYTICS / DASHBOARD API
# ═══════════════════════════════════════════════════════════

@frappe.whitelist()
def get_dashboard_stats():
    """Get platform-wide dashboard statistics (admin only)"""
    frappe.only_for(["System Manager", "Retreat Manager"])

    total_retreats = frappe.db.count("Retreat", {"status": "Active"})
    total_bookings = frappe.db.count("Retreat Booking")
    total_revenue = frappe.db.sql(
        "SELECT COALESCE(SUM(total_amount), 0) FROM `tabRetreat Booking` "
        "WHERE status IN ('Confirmed', 'Completed')"
    )[0][0]
    total_healers = frappe.db.count("Healer", {"status": "Active"})
    total_customers = frappe.db.count("Retreat Booking", {"status": ["!=", "Cancelled"]})
    avg_rating = frappe.db.sql(
        "SELECT COALESCE(AVG(average_rating), 0) FROM `tabRetreat` WHERE status='Active'"
    )[0][0]

    # Monthly booking trend (last 6 months)
    monthly_trend = frappe.db.sql("""
        SELECT
            DATE_FORMAT(creation, '%%Y-%%m') as month,
            COUNT(*) as bookings,
            SUM(total_amount) as revenue
        FROM `tabRetreat Booking`
        WHERE creation >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
          AND status != 'Cancelled'
        GROUP BY DATE_FORMAT(creation, '%%Y-%%m')
        ORDER BY month
    """, as_dict=True)

    # Top retreats by bookings
    top_retreats = frappe.db.sql("""
        SELECT
            retreat,
            COUNT(*) as bookings,
            SUM(total_amount) as revenue
        FROM `tabRetreat Booking`
        WHERE status IN ('Confirmed', 'Completed')
        GROUP BY retreat
        ORDER BY bookings DESC
        LIMIT 5
    """, as_dict=True)

    return {
        "status": "success",
        "data": {
            "total_retreats": total_retreats,
            "total_bookings": total_bookings,
            "total_revenue": flt(total_revenue, 2),
            "total_healers": total_healers,
            "total_customers": total_customers,
            "avg_rating": flt(avg_rating, 1),
            "monthly_trend": monthly_trend,
            "top_retreats": top_retreats,
        },
    }
