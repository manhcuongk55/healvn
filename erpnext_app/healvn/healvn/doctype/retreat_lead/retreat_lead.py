# Copyright (c) 2025, HealVN Team and contributors
# For license information, please see license.txt

"""
HealVN — CRM & Lead Management
Full sales pipeline for retreat inquiries, lead scoring, and conversion tracking.
"""

import frappe
from frappe.model.document import Document
from frappe.utils import flt, nowdate, getdate, add_days, cint
from frappe import _
import json


class RetreatLead(Document):
    """
    DocType: Retreat Lead
    Tracks potential guests from first inquiry to booking conversion.
    Integrates with ERPNext CRM for full pipeline visibility.
    """

    def validate(self):
        self.calculate_lead_score()
        self.set_priority()

    def before_save(self):
        if self.has_value_changed("status") and self.status == "Converted":
            self.conversion_date = nowdate()

    # ─── Lead Scoring ────────────────────────────────

    def calculate_lead_score(self):
        """Score leads 0–100 based on engagement & intent signals"""
        score = 0

        # Budget indicator (+25 max)
        if self.estimated_budget:
            budget = flt(self.estimated_budget)
            if budget >= 3000:
                score += 25
            elif budget >= 1000:
                score += 18
            elif budget >= 500:
                score += 12
            else:
                score += 5

        # Engagement signals (+25 max)
        if self.ai_chat_sessions and cint(self.ai_chat_sessions) > 0:
            score += min(15, cint(self.ai_chat_sessions) * 3)
        if self.retreats_viewed and cint(self.retreats_viewed) > 0:
            score += min(10, cint(self.retreats_viewed) * 2)

        # Intent signals (+25 max)
        if self.preferred_dates:
            score += 10  # has specific dates in mind
        if self.num_guests and cint(self.num_guests) > 1:
            score += 8  # group booking
        if self.source == "Referral":
            score += 7

        # Profile completeness (+25 max)
        if self.email:
            score += 5
        if self.phone:
            score += 5
        if self.nationality:
            score += 5
        if self.wellness_goals:
            score += 5
        if self.dietary_restrictions:
            score += 5

        self.lead_score = min(100, score)

    def set_priority(self):
        if self.lead_score >= 75:
            self.priority = "Hot"
        elif self.lead_score >= 50:
            self.priority = "Warm"
        elif self.lead_score >= 25:
            self.priority = "Cool"
        else:
            self.priority = "Cold"

    # ─── Conversion ────────────────────────────────

    @frappe.whitelist()
    def convert_to_booking(self):
        """Convert lead to a retreat booking"""
        if not self.interested_retreat:
            frappe.throw(_("Please select a retreat before converting"))

        booking = frappe.new_doc("Retreat Booking")
        booking.retreat = self.interested_retreat
        booking.guest_name = self.full_name
        booking.guest_email = self.email
        booking.guest_phone = self.phone
        booking.nationality = self.nationality
        booking.num_guests = self.num_guests or 1
        booking.check_in = self.preferred_dates or add_days(nowdate(), 14)
        booking.check_out = add_days(booking.check_in, self.preferred_duration or 5)
        booking.special_requests = self.special_requests
        booking.insert(ignore_permissions=True)

        self.status = "Converted"
        self.converted_booking = booking.name
        self.conversion_date = nowdate()
        self.save()

        return {"status": "success", "booking": booking.name}

    @frappe.whitelist()
    def convert_to_erpnext_lead(self):
        """Sync to ERPNext CRM Lead"""
        if self.erpnext_lead:
            return

        lead = frappe.new_doc("Lead")
        lead.lead_name = self.full_name
        lead.email_id = self.email
        lead.phone = self.phone
        lead.source = self.source or "Website"
        lead.company_name = self.company
        lead.territory = self.preferred_province
        lead.notes = (
            f"HealVN Lead Score: {self.lead_score}\n"
            f"Interested: {self.interested_retreat or 'TBD'}\n"
            f"Budget: {self.estimated_budget}\n"
            f"Goals: {self.wellness_goals}"
        )
        lead.insert(ignore_permissions=True)
        self.db_set("erpnext_lead", lead.name)
        return lead.name


# ═══════════════════════════════════════════════════════════
# CRM Pipeline API
# ═══════════════════════════════════════════════════════════

@frappe.whitelist()
def get_lead_pipeline():
    """Get CRM pipeline overview — leads grouped by status"""
    frappe.only_for(["System Manager", "Retreat Manager", "Sales User"])

    statuses = ["New", "Contacted", "Interested", "Negotiating", "Converted", "Lost"]
    pipeline = {}

    for status in statuses:
        leads = frappe.get_all(
            "Retreat Lead",
            filters={"status": status},
            fields=["name", "full_name", "email", "lead_score", "priority",
                     "estimated_budget", "interested_retreat", "source", "creation"],
            order_by="lead_score desc",
            limit_page_length=50,
        )
        pipeline[status] = {
            "count": len(leads),
            "total_value": sum(flt(l.get("estimated_budget", 0)) for l in leads),
            "leads": leads,
        }

    # Conversion metrics
    total_leads = frappe.db.count("Retreat Lead")
    converted = frappe.db.count("Retreat Lead", {"status": "Converted"})
    conversion_rate = flt(converted / total_leads * 100, 1) if total_leads else 0

    return {
        "status": "success",
        "data": {
            "pipeline": pipeline,
            "metrics": {
                "total_leads": total_leads,
                "converted": converted,
                "conversion_rate": conversion_rate,
                "avg_lead_score": flt(
                    frappe.db.sql("SELECT AVG(lead_score) FROM `tabRetreat Lead`")[0][0] or 0, 1
                ),
            },
        },
    }


@frappe.whitelist()
def capture_lead(full_name, email=None, phone=None, source="Website",
                  interested_retreat=None, budget=None, wellness_goals=None):
    """Public API to capture leads from frontend/landing pages"""
    # Check for duplicate
    if email and frappe.db.exists("Retreat Lead", {"email": email, "status": ["!=", "Lost"]}):
        existing = frappe.db.get_value("Retreat Lead", {"email": email}, "name")
        # Update engagement
        frappe.db.set_value("Retreat Lead", existing, {
            "ai_chat_sessions": cint(frappe.db.get_value("Retreat Lead", existing, "ai_chat_sessions")) + 1,
        })
        return {"status": "exists", "lead": existing}

    lead = frappe.new_doc("Retreat Lead")
    lead.full_name = full_name
    lead.email = email
    lead.phone = phone
    lead.source = source
    lead.interested_retreat = interested_retreat
    lead.estimated_budget = flt(budget)
    lead.wellness_goals = wellness_goals
    lead.status = "New"
    lead.insert(ignore_permissions=True)

    return {"status": "success", "lead": lead.name, "lead_score": lead.lead_score}
