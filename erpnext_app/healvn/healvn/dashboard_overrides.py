# Copyright (c) 2025, HealVN Team and contributors
"""HealVN — Dashboard Overrides for ERPNext standard DocTypes"""

import frappe
from frappe import _


def customer_dashboard(data):
    """Add HealVN booking data to Customer dashboard"""
    data["transactions"].append({
        "label": _("Wellness"),
        "items": ["Retreat Booking", "Wellness Journey"],
    })
    data["non_standard_fieldnames"] = data.get("non_standard_fieldnames", {})
    data["non_standard_fieldnames"]["Retreat Booking"] = "customer"
    return data


def supplier_dashboard(data):
    """Add HealVN healer/expense data to Supplier dashboard"""
    data["transactions"].append({
        "label": _("HealVN"),
        "items": ["Healer", "Retreat Expense"],
    })
    data["non_standard_fieldnames"] = data.get("non_standard_fieldnames", {})
    data["non_standard_fieldnames"]["Healer"] = "supplier"
    data["non_standard_fieldnames"]["Retreat Expense"] = "vendor"
    return data
