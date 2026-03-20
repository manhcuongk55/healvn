# Copyright (c) 2025, HealVN Team and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt
from frappe import _


class Healer(Document):
    """
    DocType: Healer
    Represents a wellness practitioner (yoga teacher, Đông y doctor, chef,
    therapist, meditation guide) available through the HealVN platform.
    Links to ERPNext Supplier or Employee.
    """

    def validate(self):
        self.validate_credentials()
        self.calculate_rating()

    def validate_credentials(self):
        if self.trust_verified and not self.credentials:
            frappe.throw(_("Credentials must be provided for verified healers"))

    def calculate_rating(self):
        if self.reviews:
            total = sum(flt(r.rating) for r in self.reviews)
            self.average_rating = flt(total / len(self.reviews), 1)
            self.total_reviews = len(self.reviews)

    def get_availability(self, date, retreat=None):
        """Check healer availability for a date"""
        filters = {
            "healer": self.name,
            "date": date,
            "status": ["in", ["Confirmed", "In Progress"]],
        }
        if retreat:
            filters["retreat"] = retreat
        booked = frappe.db.count("Healer Session", filters)
        return booked < (self.max_daily_sessions or 3)

    def as_profile_dict(self):
        return {
            "name": self.name,
            "healer_name": self.healer_name,
            "specialty": self.specialty,
            "sub_specialties": [s.sub_specialty for s in (self.sub_specialties or [])],
            "bio": self.bio,
            "experience_years": self.experience_years,
            "daily_rate": self.daily_rate,
            "session_rate": self.session_rate,
            "currency": self.currency or "USD",
            "languages": [l.language for l in (self.languages or [])],
            "retreats": [r.retreat for r in (self.linked_retreats or [])],
            "average_rating": self.average_rating,
            "total_reviews": self.total_reviews,
            "trust_verified": self.trust_verified,
            "photo": self.photo,
            "province": self.province,
        }
