# Copyright (c) 2025, HealVN Team and contributors
# For license information, please see license.txt

"""
HealVN — Retreat Expense Tracking
Track all operational expenses per retreat: supplies, healer payments,
maintenance, marketing, and generate P&L per retreat.
"""

import frappe
from frappe.model.document import Document
from frappe.utils import flt, nowdate
from frappe import _


class RetreatExpense(Document):
    """
    DocType: Retreat Expense
    Tracks operational expenses linked to specific retreats.
    Auto-creates ERPNext Journal Entry on approval.
    """

    def validate(self):
        if self.amount and self.amount < 0:
            frappe.throw(_("Expense amount cannot be negative"))
        if not self.expense_date:
            self.expense_date = nowdate()

    def on_submit(self):
        self.create_journal_entry()

    def on_cancel(self):
        if self.journal_entry:
            je = frappe.get_doc("Journal Entry", self.journal_entry)
            if je.docstatus == 1:
                je.cancel()

    def create_journal_entry(self):
        """Create Journal Entry for the expense"""
        company = frappe.defaults.get_user_default("Company") or "HealVN Co., Ltd"
        abbr = frappe.db.get_value("Company", company, "abbr") or "HVN"

        expense_map = {
            "Healer Payment": f"Healer Payments - {abbr}",
            "Partner Payout": f"Retreat Partner Payouts - {abbr}",
            "Supplies": f"Direct Expenses - {abbr}",
            "Marketing": f"Marketing & Influencer - {abbr}",
            "Maintenance": f"Direct Expenses - {abbr}",
            "Content Production": f"Video Content Production - {abbr}",
            "Inspection": f"Travel & Inspection - {abbr}",
            "Technology": f"AI Infrastructure - {abbr}",
            "Other": f"Indirect Expenses - {abbr}",
        }

        expense_account = expense_map.get(self.expense_type, f"Indirect Expenses - {abbr}")

        je = frappe.new_doc("Journal Entry")
        je.posting_date = self.expense_date
        je.company = company
        je.user_remark = f"HealVN Expense: {self.description} (Retreat: {self.retreat or 'General'})"

        je.append("accounts", {
            "account": expense_account,
            "debit_in_account_currency": self.amount,
            "cost_center": f"Retreat Operations - {abbr}",
        })
        je.append("accounts", {
            "account": frappe.db.get_value("Company", company, "default_bank_account")
                        or f"Cash - {abbr}",
            "credit_in_account_currency": self.amount,
        })

        je.insert(ignore_permissions=True)
        je.submit()
        self.db_set("journal_entry", je.name)


# ═══════════════════════════════════════════════════════════
# Retreat P&L (Profit & Loss)
# ═══════════════════════════════════════════════════════════

@frappe.whitelist()
def get_retreat_pnl(retreat_name, from_date=None, to_date=None):
    """
    Calculate Profit & Loss for a specific retreat.
    Revenue = confirmed bookings
    Expenses = linked retreat expenses
    """
    frappe.only_for(["System Manager", "Retreat Manager"])

    if not from_date:
        from_date = frappe.utils.get_first_day(nowdate())
    if not to_date:
        to_date = nowdate()

    # Revenue
    revenue = frappe.db.sql("""
        SELECT
            COALESCE(SUM(total_amount), 0) as total_revenue,
            COUNT(*) as total_bookings,
            COALESCE(AVG(total_amount), 0) as avg_booking_value
        FROM `tabRetreat Booking`
        WHERE retreat = %s
          AND status IN ('Confirmed', 'Completed')
          AND check_in BETWEEN %s AND %s
    """, (retreat_name, from_date, to_date), as_dict=True)[0]

    # Expenses by type
    expenses = frappe.db.sql("""
        SELECT
            expense_type,
            COALESCE(SUM(amount), 0) as total,
            COUNT(*) as count
        FROM `tabRetreat Expense`
        WHERE retreat = %s
          AND expense_date BETWEEN %s AND %s
          AND docstatus = 1
        GROUP BY expense_type
        ORDER BY total DESC
    """, (retreat_name, from_date, to_date), as_dict=True)

    total_expenses = sum(flt(e.total) for e in expenses)

    # Commission
    commission_rate = 0.15
    commission = flt(revenue.total_revenue * commission_rate, 2)

    # Net profit
    net_profit = flt(commission - total_expenses, 2)
    margin = flt(net_profit / commission * 100, 1) if commission else 0

    return {
        "status": "success",
        "data": {
            "retreat": retreat_name,
            "period": {"from": str(from_date), "to": str(to_date)},
            "revenue": {
                "gross_booking_revenue": flt(revenue.total_revenue, 2),
                "platform_commission": commission,
                "total_bookings": revenue.total_bookings,
                "avg_booking_value": flt(revenue.avg_booking_value, 2),
            },
            "expenses": {
                "by_type": expenses,
                "total": flt(total_expenses, 2),
            },
            "profit": {
                "net_profit": net_profit,
                "margin_pct": margin,
            },
        },
    }
