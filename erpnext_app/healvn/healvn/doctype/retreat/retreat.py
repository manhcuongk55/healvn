# Copyright (c) 2025, HealVN Team and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt, nowdate, getdate, add_days
from frappe import _


class Retreat(Document):
    """
    DocType: Retreat
    Represents a wellness retreat property listed on HealVN marketplace.
    Links to ERPNext Item for booking as a purchasable service.
    """

    def validate(self):
        self.validate_pricing()
        self.validate_capacity()
        self.validate_location()
        self.update_verification_progress()

    def before_save(self):
        if not self.item_code:
            self.create_linked_item()
        self.calculate_average_rating()

    def on_update(self):
        self.update_linked_item()

    # ─── Validation ──────────────────────────────────────────

    def validate_pricing(self):
        if self.price_per_night and self.price_per_night < 0:
            frappe.throw(_("Price per night cannot be negative"))
        if self.price_per_package and self.price_per_package < 0:
            frappe.throw(_("Package price cannot be negative"))
        if not self.price_per_night and not self.price_per_package:
            frappe.throw(_("At least one pricing option (per night or package) must be set"))

    def validate_capacity(self):
        if self.max_guests and self.max_guests < 1:
            frappe.throw(_("Maximum guests must be at least 1"))

    def validate_location(self):
        if self.latitude and (self.latitude < -90 or self.latitude > 90):
            frappe.throw(_("Invalid latitude value"))
        if self.longitude and (self.longitude < -180 or self.longitude > 180):
            frappe.throw(_("Invalid longitude value"))

    def update_verification_progress(self):
        """Calculate 7-layer verification progress (0–100%)"""
        layers = [
            self.identity_verified,
            self.legal_verified,
            self.physical_inspected,
            self.photo_audited,
            self.review_verified,
            self.price_transparent,
            self.ongoing_monitored,
        ]
        verified_count = sum(1 for layer in layers if layer)
        self.verification_score = flt(verified_count / 7 * 100, 1)
        self.verification_status = (
            "Fully Verified" if verified_count == 7
            else "Partially Verified" if verified_count >= 4
            else "Pending Verification"
        )

    # ─── Linked ERPNext Item ──────────────────────────────────

    def create_linked_item(self):
        """Auto-create an ERPNext Item for this retreat (service type)"""
        item = frappe.new_doc("Item")
        item.item_code = f"RET-{self.name}"
        item.item_name = self.retreat_name
        item.item_group = "Retreat Services"
        item.is_stock_item = 0  # service, not stock
        item.stock_uom = "Nos"
        item.description = self.description or self.retreat_name
        item.standard_rate = self.price_per_night or self.price_per_package or 0
        item.insert(ignore_permissions=True)
        self.item_code = item.item_code

    def update_linked_item(self):
        """Keep linked Item in sync with retreat pricing"""
        if self.item_code and frappe.db.exists("Item", self.item_code):
            frappe.db.set_value("Item", self.item_code, {
                "item_name": self.retreat_name,
                "standard_rate": self.price_per_night or self.price_per_package or 0,
                "description": self.description or self.retreat_name,
            })

    # ─── Rating ───────────────────────────────────────────────

    def calculate_average_rating(self):
        """Pull average rating from Retreat Review child table"""
        if self.reviews:
            total = sum(flt(r.rating) for r in self.reviews)
            self.average_rating = flt(total / len(self.reviews), 1)
            self.total_reviews = len(self.reviews)
        else:
            self.average_rating = 0
            self.total_reviews = 0

    # ─── Availability ─────────────────────────────────────────

    def check_availability(self, check_in, check_out):
        """Check if retreat has availability for given dates"""
        check_in = getdate(check_in)
        check_out = getdate(check_out)

        if check_in >= check_out:
            frappe.throw(_("Check-out date must be after check-in date"))

        # Count overlapping confirmed bookings
        overlapping = frappe.db.count("Retreat Booking", filters={
            "retreat": self.name,
            "status": ["in", ["Confirmed", "Checked In"]],
            "check_in": ["<", check_out],
            "check_out": [">", check_in],
        })

        available_slots = (self.max_guests or 1) - overlapping
        return {
            "available": available_slots > 0,
            "slots_remaining": max(0, available_slots),
            "max_guests": self.max_guests or 1,
        }

    # ─── API Helper ───────────────────────────────────────────

    def as_marketplace_dict(self):
        """Return retreat data formatted for frontend marketplace"""
        return {
            "name": self.name,
            "retreat_name": self.retreat_name,
            "location": self.location,
            "province": self.province,
            "country": self.country or "Vietnam",
            "category": self.category,
            "wellness_types": [wt.wellness_type for wt in (self.wellness_types or [])],
            "price_per_night": self.price_per_night,
            "price_per_package": self.price_per_package,
            "package_duration_days": self.package_duration_days,
            "currency": self.currency or "USD",
            "average_rating": self.average_rating,
            "total_reviews": self.total_reviews,
            "verification_status": self.verification_status,
            "verification_score": self.verification_score,
            "thumbnail": self.thumbnail,
            "photos": [p.photo for p in (self.photos or [])],
            "short_description": (self.description or "")[:200],
            "max_guests": self.max_guests,
            "amenities": [a.amenity for a in (self.amenities or [])],
            "latitude": self.latitude,
            "longitude": self.longitude,
        }
