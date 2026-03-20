# Copyright (c) 2025, HealVN Team and contributors
"""HealVN — Boot Session: inject platform config into client"""

import frappe


def boot_session(bootinfo):
    """Add HealVN config to the boot object (available in client JS)"""
    bootinfo.healvn = {
        "version": "2.0.0",
        "platform_name": "HealVN",
        "commission_rate": 0.15,
        "default_currency": "VND",
        "support_email": "hello@healvn.com",
        "support_phone": "+84 123 456 789",
        "features": {
            "ai_advisor": True,
            "video_feed": True,
            "trust_verification": True,
            "wellness_journey": True,
            "lead_scoring": True,
        },
        "stats": {
            "total_retreats": frappe.db.count("Retreat", {"status": "Active"}) if frappe.db.table_exists("tabRetreat") else 0,
            "total_healers": frappe.db.count("Healer", {"status": "Active"}) if frappe.db.table_exists("tabHealer") else 0,
        },
    }
