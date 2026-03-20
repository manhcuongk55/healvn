# Copyright (c) 2025, HealVN Team and contributors
# For license information, please see license.txt

"""
HealVN — Retreat Package Management
Pre-designed wellness packages combining retreat stay, healer sessions,
meals, and activities into a single bookable product.
"""

import frappe
from frappe.model.document import Document
from frappe.utils import flt, nowdate
from frappe import _


class RetreatPackage(Document):
    """
    DocType: Retreat Package
    All-inclusive wellness packages (e.g., 5-day detox, 7-day yoga immersion).
    Bundles retreat stay + healer sessions + meals + activities.
    """

    def validate(self):
        self.calculate_pricing()
        self.validate_items()

    def before_save(self):
        if not self.item_code:
            self.create_linked_item()

    def calculate_pricing(self):
        """Calculate total package cost from components"""
        total_cost = 0

        # Accommodation cost
        if self.retreat and self.duration_nights:
            retreat = frappe.get_doc("Retreat", self.retreat)
            if retreat.price_per_night:
                total_cost += flt(retreat.price_per_night) * self.duration_nights

        # Healer session costs
        for session in (self.healer_sessions or []):
            total_cost += flt(session.session_rate) * cint(session.num_sessions)

        # Activity costs
        for activity in (self.included_activities or []):
            total_cost += flt(activity.cost)

        # Meal plan cost
        total_cost += flt(self.meal_plan_cost or 0)

        # Transport cost
        total_cost += flt(self.transport_cost or 0)

        self.base_cost = flt(total_cost, 2)
        self.margin_amount = flt(self.base_cost * flt(self.margin_pct or 20) / 100, 2)
        self.selling_price = flt(self.base_cost + self.margin_amount, 2)

        # Discount
        if self.discount_pct:
            self.discount_amount = flt(self.selling_price * self.discount_pct / 100, 2)
        self.final_price = flt(self.selling_price - flt(self.discount_amount or 0), 2)

    def validate_items(self):
        if not self.retreat:
            frappe.throw(_("A retreat must be linked to the package"))
        if not self.duration_nights or self.duration_nights < 1:
            frappe.throw(_("Package must be at least 1 night"))

    def create_linked_item(self):
        """Create ERPNext Item for this package"""
        item = frappe.new_doc("Item")
        item.item_code = f"PKG-{self.name}"
        item.item_name = self.package_name
        item.item_group = "Wellness Packages"
        item.is_stock_item = 0
        item.stock_uom = "Nos"
        item.standard_rate = self.final_price
        item.description = self.description or self.package_name
        item.insert(ignore_permissions=True)
        self.item_code = item.item_code


def cint(val):
    return int(val or 0)


# ═══════════════════════════════════════════════════════════
# Package API
# ═══════════════════════════════════════════════════════════

@frappe.whitelist(allow_guest=True)
def get_packages(retreat=None, category=None, max_price=None, min_duration=None):
    """Get available wellness packages"""
    filters = {"status": "Active"}
    if retreat:
        filters["retreat"] = retreat
    if category:
        filters["category"] = category

    packages = frappe.get_all(
        "Retreat Package",
        filters=filters,
        fields=[
            "name", "package_name", "retreat", "category",
            "duration_nights", "max_guests", "final_price",
            "currency", "description", "thumbnail",
            "includes_meals", "includes_transport", "includes_healer",
        ],
        order_by="final_price asc",
    )

    if max_price:
        packages = [p for p in packages if flt(p.final_price) <= flt(max_price)]
    if min_duration:
        packages = [p for p in packages if p.duration_nights >= int(min_duration)]

    # Enrich with retreat name
    for p in packages:
        p["retreat_name"] = frappe.db.get_value("Retreat", p["retreat"], "retreat_name")

    return {"status": "success", "data": packages}
