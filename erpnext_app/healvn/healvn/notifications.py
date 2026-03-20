# Copyright (c) 2025, HealVN Team and contributors
"""HealVN — Notification Configuration"""

import frappe


def get_notification_config():
    return {
        "for_doctype": {
            "Retreat Booking": {"status": ("in", ("Pending",))},
            "Retreat Lead": {"status": ("in", ("New",))},
            "Retreat Expense": {"docstatus": 0, "workflow_state": "Under Review"},
            "Retreat": {"status": "Draft"},
            "Healer": {"status": "Pending Approval"},
        },
    }
