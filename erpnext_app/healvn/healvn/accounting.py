# Copyright (c) 2025, HealVN Team and contributors
# For license information, please see license.txt

"""
HealVN — ERPNext Accounting & Finance Configuration
Chart of Accounts, Tax Templates, Payment Terms, Company Settings
for Wellness Tourism Business Operations.
"""

import frappe
from frappe import _
from frappe.utils import flt


def setup_accounting(company_name="HealVN Co., Ltd"):
    """Full accounting setup for wellness tourism company"""
    create_company(company_name)
    create_cost_centers(company_name)
    create_chart_of_accounts(company_name)
    create_tax_templates(company_name)
    create_payment_terms()
    create_price_lists()
    create_item_groups()
    create_mode_of_payments()
    frappe.msgprint(_("🌿 HealVN Accounting setup complete!"))


def create_company(company_name):
    """Create HealVN company with Vietnam settings"""
    if frappe.db.exists("Company", company_name):
        return

    company = frappe.new_doc("Company")
    company.company_name = company_name
    company.abbr = "HVN"
    company.country = "Vietnam"
    company.default_currency = "VND"
    company.chart_of_accounts = "Standard"
    company.default_holiday_list = ""
    company.domain = "Services"
    company.insert(ignore_permissions=True)


def create_cost_centers(company_name):
    """Create cost centers for retreat operations"""
    abbr = "HVN"
    cost_centers = [
        {"name": f"Retreat Operations - {abbr}", "parent": f"{company_name} - {abbr}"},
        {"name": f"Marketing & Content - {abbr}", "parent": f"{company_name} - {abbr}"},
        {"name": f"AI & Technology - {abbr}", "parent": f"{company_name} - {abbr}"},
        {"name": f"Trust & Verification - {abbr}", "parent": f"{company_name} - {abbr}"},
        {"name": f"Healer Network - {abbr}", "parent": f"{company_name} - {abbr}"},
        {"name": f"Corporate Wellness - {abbr}", "parent": f"{company_name} - {abbr}"},
        {"name": f"Admin & HR - {abbr}", "parent": f"{company_name} - {abbr}"},
    ]
    for cc in cost_centers:
        if not frappe.db.exists("Cost Center", cc["name"]):
            doc = frappe.new_doc("Cost Center")
            doc.cost_center_name = cc["name"].replace(f" - {abbr}", "")
            doc.parent_cost_center = cc["parent"]
            doc.company = company_name
            doc.insert(ignore_permissions=True)


def create_chart_of_accounts(company_name):
    """Create custom account heads for retreat business"""
    abbr = "HVN"
    accounts = [
        # Revenue accounts
        {"account_name": "Booking Revenue", "parent": f"Direct Income - {abbr}", "type": "Income Account"},
        {"account_name": "Commission Income", "parent": f"Direct Income - {abbr}", "type": "Income Account"},
        {"account_name": "AI Subscription Revenue", "parent": f"Direct Income - {abbr}", "type": "Income Account"},
        {"account_name": "Corporate Wellness Revenue", "parent": f"Direct Income - {abbr}", "type": "Income Account"},
        {"account_name": "Healer Session Revenue", "parent": f"Direct Income - {abbr}", "type": "Income Account"},
        {"account_name": "Content & Sponsored Revenue", "parent": f"Indirect Income - {abbr}", "type": "Income Account"},

        # Expense accounts
        {"account_name": "Retreat Partner Payouts", "parent": f"Direct Expenses - {abbr}", "type": "Expense Account"},
        {"account_name": "Healer Payments", "parent": f"Direct Expenses - {abbr}", "type": "Expense Account"},
        {"account_name": "Trust Verification Costs", "parent": f"Direct Expenses - {abbr}", "type": "Expense Account"},
        {"account_name": "AI Infrastructure", "parent": f"Direct Expenses - {abbr}", "type": "Expense Account"},
        {"account_name": "Marketing & Influencer", "parent": f"Indirect Expenses - {abbr}", "type": "Expense Account"},
        {"account_name": "Video Content Production", "parent": f"Indirect Expenses - {abbr}", "type": "Expense Account"},
        {"account_name": "Cloud & Hosting", "parent": f"Indirect Expenses - {abbr}", "type": "Expense Account"},
        {"account_name": "Travel & Inspection", "parent": f"Indirect Expenses - {abbr}", "type": "Expense Account"},
    ]
    for acc in accounts:
        full_name = f"{acc['account_name']} - {abbr}"
        if not frappe.db.exists("Account", full_name):
            doc = frappe.new_doc("Account")
            doc.account_name = acc["account_name"]
            doc.parent_account = acc["parent"]
            doc.company = company_name
            doc.account_type = acc.get("type", "")
            doc.insert(ignore_permissions=True)


def create_tax_templates(company_name):
    """Create Vietnam VAT templates"""
    abbr = "HVN"
    templates = [
        {
            "title": "Vietnam VAT 10%",
            "taxes": [{"charge_type": "On Net Total", "account_head": f"VAT - {abbr}", "rate": 10, "description": "VAT 10% — Dịch vụ du lịch"}],
        },
        {
            "title": "Vietnam VAT 8%",
            "taxes": [{"charge_type": "On Net Total", "account_head": f"VAT - {abbr}", "rate": 8, "description": "VAT 8% — Dịch vụ lưu trú (ưu đãi)"}],
        },
        {
            "title": "Export Service (0% VAT)",
            "taxes": [{"charge_type": "On Net Total", "account_head": f"VAT - {abbr}", "rate": 0, "description": "Export Service — 0% VAT for international bookings"}],
        },
    ]
    for tmpl in templates:
        if not frappe.db.exists("Sales Taxes and Charges Template", {"title": tmpl["title"], "company": company_name}):
            doc = frappe.new_doc("Sales Taxes and Charges Template")
            doc.title = tmpl["title"]
            doc.company = company_name
            for tax in tmpl["taxes"]:
                doc.append("taxes", tax)
            doc.insert(ignore_permissions=True)


def create_payment_terms():
    """Create payment terms for retreat bookings"""
    terms = [
        {
            "name": "Retreat Booking — 50/50",
            "terms": [
                {"payment_term_name": "Deposit", "invoice_portion": 50, "credit_days": 0, "description": "50% deposit on booking confirmation"},
                {"payment_term_name": "Balance", "invoice_portion": 50, "credit_days": 30, "description": "50% balance before check-in"},
            ],
        },
        {
            "name": "Retreat Booking — Full Upfront",
            "terms": [
                {"payment_term_name": "Full Payment", "invoice_portion": 100, "credit_days": 0, "description": "100% payment on booking"},
            ],
        },
        {
            "name": "Corporate Wellness — Net 30",
            "terms": [
                {"payment_term_name": "Net 30", "invoice_portion": 100, "credit_days": 30, "description": "Payment within 30 days of invoice"},
            ],
        },
        {
            "name": "Partner Payout — Weekly",
            "terms": [
                {"payment_term_name": "Weekly Payout", "invoice_portion": 100, "credit_days": 7, "description": "Weekly payout to retreat partners"},
            ],
        },
    ]
    for term_data in terms:
        pt_name = term_data["name"]
        if not frappe.db.exists("Payment Terms Template", pt_name):
            doc = frappe.new_doc("Payment Terms Template")
            doc.template_name = pt_name
            for t in term_data["terms"]:
                doc.append("terms", t)
            doc.insert(ignore_permissions=True)


def create_price_lists():
    """Create price lists for different markets"""
    lists = [
        {"name": "HealVN Standard (VND)", "currency": "VND"},
        {"name": "HealVN International (USD)", "currency": "USD"},
        {"name": "HealVN Corporate", "currency": "USD"},
        {"name": "HealVN Partner Cost", "currency": "VND"},
    ]
    for pl in lists:
        if not frappe.db.exists("Price List", pl["name"]):
            doc = frappe.new_doc("Price List")
            doc.price_list_name = pl["name"]
            doc.currency = pl["currency"]
            doc.selling = 1
            doc.insert(ignore_permissions=True)


def create_item_groups():
    """Create item groups for retreat services"""
    groups = [
        {"name": "Retreat Services", "parent": "Services"},
        {"name": "Yoga & Meditation", "parent": "Retreat Services"},
        {"name": "Spa & Massage", "parent": "Retreat Services"},
        {"name": "Detox Programs", "parent": "Retreat Services"},
        {"name": "Cultural Experiences", "parent": "Retreat Services"},
        {"name": "Adventure Activities", "parent": "Retreat Services"},
        {"name": "Healer Sessions", "parent": "Retreat Services"},
        {"name": "Wellness Packages", "parent": "Retreat Services"},
        {"name": "Corporate Wellness", "parent": "Retreat Services"},
        {"name": "Wellness Products", "parent": "Products"},
        {"name": "Organic Food & Beverages", "parent": "Wellness Products"},
        {"name": "Spa Supplies", "parent": "Wellness Products"},
        {"name": "Yoga Equipment", "parent": "Wellness Products"},
    ]
    for g in groups:
        if not frappe.db.exists("Item Group", g["name"]):
            doc = frappe.new_doc("Item Group")
            doc.item_group_name = g["name"]
            doc.parent_item_group = g["parent"]
            doc.insert(ignore_permissions=True)


def create_mode_of_payments():
    """Create payment methods"""
    modes = [
        "VNPay", "MoMo", "ZaloPay",
        "Bank Transfer (VND)", "Bank Transfer (USD)",
        "Visa / Mastercard", "PayPal",
        "Cash (VND)", "Cash (USD)",
        "Crypto (USDT)",
    ]
    for mode in modes:
        if not frappe.db.exists("Mode of Payment", mode):
            doc = frappe.new_doc("Mode of Payment")
            doc.mode_of_payment = mode
            doc.type = "General" if "Bank" not in mode else "Bank"
            doc.insert(ignore_permissions=True)
