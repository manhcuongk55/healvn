# Copyright (c) 2025, HealVN Team and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt, nowdate, getdate, add_days
from frappe import _
import json


class WellnessJourney(Document):
    """
    DocType: Wellness Journey
    AI-generated personalized wellness plan for a guest.
    Contains multi-day itinerary, linked retreats, healers, and wellness scoring.
    """

    def validate(self):
        self.validate_dates()
        self.calculate_wellness_score()
        self.validate_itinerary()

    def validate_dates(self):
        if self.start_date and self.end_date:
            if getdate(self.start_date) > getdate(self.end_date):
                frappe.throw(_("End date must be after start date"))

    def calculate_wellness_score(self):
        """Calculate composite wellness score from sub-dimensions"""
        dimensions = {
            "physical_score": flt(self.physical_score or 0),
            "mental_score": flt(self.mental_score or 0),
            "emotional_score": flt(self.emotional_score or 0),
            "social_score": flt(self.social_score or 0),
            "spiritual_score": flt(self.spiritual_score or 0),
        }
        active = [v for v in dimensions.values() if v > 0]
        self.overall_score = flt(sum(active) / len(active), 1) if active else 0

    def validate_itinerary(self):
        """Validate JSON itinerary structure"""
        if self.itinerary_json:
            try:
                data = json.loads(self.itinerary_json)
                if not isinstance(data, list):
                    frappe.throw(_("Itinerary must be a JSON array of daily plans"))
            except json.JSONDecodeError:
                frappe.throw(_("Invalid JSON in itinerary"))

    # ─── AI Journey Generation ────────────────────────────────

    @frappe.whitelist()
    def generate_ai_journey(self):
        """Generate AI-powered wellness journey plan"""
        guest_profile = self.get_guest_profile()
        available_retreats = self.get_matching_retreats()
        available_healers = self.get_matching_healers()

        itinerary = self.build_itinerary(
            guest_profile, available_retreats, available_healers
        )

        self.itinerary_json = json.dumps(itinerary, ensure_ascii=False, indent=2)
        self.ai_generated = 1
        self.generation_date = nowdate()
        self.save()

        return {"status": "success", "itinerary": itinerary}

    def get_guest_profile(self):
        """Build guest profile for AI recommendation"""
        return {
            "name": self.guest_name,
            "stress_level": self.stress_level,
            "physical_score": self.physical_score,
            "mental_score": self.mental_score,
            "budget": self.budget,
            "duration_days": self.duration_days,
            "preferences": [p.preference for p in (self.preferences or [])],
            "wellness_goals": [g.goal for g in (self.wellness_goals or [])],
            "dietary_restrictions": self.dietary_restrictions,
            "mobility_level": self.mobility_level,
        }

    def get_matching_retreats(self):
        """Find retreats matching guest preferences and budget"""
        filters = {
            "status": "Active",
            "verification_status": ["in", ["Fully Verified", "Partially Verified"]],
        }

        if self.preferred_province:
            filters["province"] = self.preferred_province

        retreats = frappe.get_all(
            "Retreat",
            filters=filters,
            fields=[
                "name", "retreat_name", "location", "province",
                "category", "price_per_night", "price_per_package",
                "average_rating", "verification_score",
            ],
            order_by="average_rating desc, verification_score desc",
            limit_page_length=20,
        )

        # Filter by budget
        if self.budget:
            retreats = [
                r for r in retreats
                if (r.price_per_night or 0) * (self.duration_days or 1) <= self.budget
                or (r.price_per_package or 0) <= self.budget
            ]

        return retreats

    def get_matching_healers(self):
        """Find healers matching wellness goals"""
        filters = {"status": "Active", "trust_verified": 1}

        if self.preferred_province:
            # Healers linked to retreats in preferred province
            pass

        healers = frappe.get_all(
            "Healer",
            filters=filters,
            fields=[
                "name", "healer_name", "specialty",
                "session_rate", "average_rating",
            ],
            order_by="average_rating desc",
            limit_page_length=10,
        )
        return healers

    def build_itinerary(self, profile, retreats, healers):
        """Build a day-by-day itinerary from available data"""
        days = self.duration_days or 5
        itinerary = []

        primary_retreat = retreats[0] if retreats else None

        for day in range(1, days + 1):
            daily = {
                "day": day,
                "date": str(add_days(getdate(self.start_date or nowdate()), day - 1)),
                "theme": self.get_day_theme(day, days),
                "activities": [],
            }

            # Morning: Yoga / Meditation
            daily["activities"].append({
                "time": "06:00",
                "activity": "Sunrise Yoga & Breathing",
                "type": "yoga",
                "duration_minutes": 60,
                "healer": healers[0]["healer_name"] if healers else "House Instructor",
            })

            # Breakfast
            daily["activities"].append({
                "time": "07:30",
                "activity": "Organic Wellness Breakfast",
                "type": "dining",
                "duration_minutes": 45,
                "notes": "Farm-to-table organic menu",
            })

            # Mid-morning: Main therapy based on day theme
            therapy = self.get_main_therapy(day, days, healers)
            daily["activities"].append(therapy)

            # Lunch
            daily["activities"].append({
                "time": "12:00",
                "activity": "Vietnamese Wellness Lunch",
                "type": "dining",
                "duration_minutes": 60,
            })

            # Afternoon: Activity
            daily["activities"].append({
                "time": "14:00",
                "activity": self.get_afternoon_activity(day, days),
                "type": "activity",
                "duration_minutes": 120,
            })

            # Evening: Relaxation
            daily["activities"].append({
                "time": "17:00",
                "activity": "Sunset Meditation & Tea Ceremony",
                "type": "meditation",
                "duration_minutes": 45,
            })

            daily["retreat"] = primary_retreat["retreat_name"] if primary_retreat else None
            itinerary.append(daily)

        return itinerary

    def get_day_theme(self, day, total_days):
        themes = {
            1: "Arrival & Grounding",
            2: "Deep Relaxation",
            3: "Inner Exploration",
            4: "Cultural Immersion",
            5: "Renewal & Integration",
        }
        if day == 1:
            return "Arrival & Grounding"
        if day == total_days:
            return "Renewal & Departure"
        idx = ((day - 1) % 4) + 2
        return list(themes.values())[min(idx, len(themes) - 1)]

    def get_main_therapy(self, day, total_days, healers):
        therapies = [
            {"activity": "Traditional Vietnamese Herbal Massage", "type": "spa"},
            {"activity": "Hot Stone Therapy (Đá Nóng)", "type": "spa"},
            {"activity": "Đông Y Consultation & Acupuncture", "type": "traditional"},
            {"activity": "Sound Healing & Bowl Therapy", "type": "sound"},
            {"activity": "Aromatherapy & Reflexology", "type": "spa"},
        ]
        therapy = therapies[(day - 1) % len(therapies)]
        therapy["time"] = "09:30"
        therapy["duration_minutes"] = 90
        therapy["healer"] = healers[min(day - 1, len(healers) - 1)]["healer_name"] if healers else "Expert Therapist"
        return therapy

    def get_afternoon_activity(self, day, total_days):
        activities = [
            "Nature Walk & Forest Bathing",
            "Organic Farm Visit & Cooking Class",
            "Kayaking / Stand-up Paddle",
            "Traditional Village Tour & Handicraft",
            "Beach Yoga & Sand Meditation",
        ]
        return activities[(day - 1) % len(activities)]

    # ─── API ──────────────────────────────────────────────────

    def as_journey_dict(self):
        return {
            "name": self.name,
            "guest_name": self.guest_name,
            "start_date": str(self.start_date) if self.start_date else None,
            "end_date": str(self.end_date) if self.end_date else None,
            "duration_days": self.duration_days,
            "overall_score": self.overall_score,
            "physical_score": self.physical_score,
            "mental_score": self.mental_score,
            "emotional_score": self.emotional_score,
            "social_score": self.social_score,
            "spiritual_score": self.spiritual_score,
            "itinerary": json.loads(self.itinerary_json) if self.itinerary_json else [],
            "ai_generated": self.ai_generated,
            "budget": self.budget,
            "status": self.status,
        }
