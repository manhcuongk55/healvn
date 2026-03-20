# Copyright (c) 2025, HealVN Team and contributors
# For license information, please see license.txt

"""
HealVN — Post-install setup and initial data.
"""

import frappe
from frappe import _


def after_install():
    """Run after HealVN app is installed on a site"""
    create_item_group()
    create_custom_roles()
    create_territories()
    create_workspace()
    frappe.msgprint(_("🌿 HealVN installed successfully!"))


def create_item_group():
    """Create 'Retreat Services' item group"""
    if not frappe.db.exists("Item Group", "Retreat Services"):
        group = frappe.new_doc("Item Group")
        group.item_group_name = "Retreat Services"
        group.parent_item_group = "Services"
        group.insert(ignore_permissions=True)


def create_custom_roles():
    """Create HealVN-specific roles"""
    roles = [
        {"role_name": "Retreat Manager", "desk_access": 1},
        {"role_name": "Retreat Owner", "desk_access": 1},
        {"role_name": "Healer", "desk_access": 1},
        {"role_name": "Wellness Advisor", "desk_access": 1},
    ]
    for role in roles:
        if not frappe.db.exists("Role", role["role_name"]):
            doc = frappe.new_doc("Role")
            doc.role_name = role["role_name"]
            doc.desk_access = role.get("desk_access", 0)
            doc.insert(ignore_permissions=True)


def create_territories():
    """Create Vietnam provinces as territories"""
    provinces = [
        "Hà Nội", "TP. Hồ Chí Minh", "Đà Nẵng", "Hải Phòng",
        "Phú Quốc", "Kiên Giang", "Khánh Hòa", "Quảng Nam",
        "Lào Cai", "Hà Giang", "Sơn La", "Lâm Đồng",
        "Bà Rịa-Vũng Tàu", "Bình Thuận", "Ninh Bình",
        "Quảng Ninh", "Thừa Thiên Huế", "Nghệ An",
    ]
    for prov in provinces:
        if not frappe.db.exists("Territory", prov):
            territory = frappe.new_doc("Territory")
            territory.territory_name = prov
            territory.parent_territory = "Vietnam"
            territory.insert(ignore_permissions=True)


def create_workspace():
    """Create HealVN workspace in ERPNext desk"""
    if frappe.db.exists("Workspace", "HealVN"):
        return

    workspace = frappe.new_doc("Workspace")
    workspace.name = "HealVN"
    workspace.label = "HealVN"
    workspace.category = "Modules"
    workspace.icon = "leaf"
    workspace.module = "HealVN"
    workspace.is_standard = 0

    shortcuts = [
        {"type": "DocType", "label": "Retreats", "link_to": "Retreat", "color": "#3ecf8e"},
        {"type": "DocType", "label": "Bookings", "link_to": "Retreat Booking", "color": "#e8c97a"},
        {"type": "DocType", "label": "Healers", "link_to": "Healer", "color": "#7ab8e8"},
        {"type": "DocType", "label": "Wellness Journeys", "link_to": "Wellness Journey", "color": "#e87a9f"},
    ]
    for sc in shortcuts:
        workspace.append("shortcuts", sc)

    workspace.insert(ignore_permissions=True)
