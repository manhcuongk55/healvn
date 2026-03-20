# Copyright (c) 2025, HealVN Team and contributors
# For license information, please see license.txt

"""
HealVN — ERPNext Workflows
Approval workflows for bookings, expenses, verification, and healer onboarding.
"""

import frappe
from frappe import _


def setup_workflows():
    """Create all HealVN business workflows"""
    create_booking_workflow()
    create_expense_workflow()
    create_verification_workflow()
    create_healer_onboarding_workflow()
    create_lead_workflow()
    frappe.msgprint(_("🌿 HealVN Workflows configured!"))


def create_booking_workflow():
    """Booking approval flow: Pending → Confirmed → Checked In → Completed"""
    if frappe.db.exists("Workflow", "Retreat Booking Workflow"):
        return

    workflow = frappe.new_doc("Workflow")
    workflow.workflow_name = "Retreat Booking Workflow"
    workflow.document_type = "Retreat Booking"
    workflow.is_active = 1
    workflow.send_email_alert = 1

    states = [
        {"state": "Pending", "doc_status": 0, "allow_edit": "Retreat Manager",
         "style": "Warning"},
        {"state": "Confirmed", "doc_status": 0, "allow_edit": "Retreat Manager",
         "style": "Primary"},
        {"state": "Checked In", "doc_status": 0, "allow_edit": "Retreat Manager",
         "style": "Info"},
        {"state": "Completed", "doc_status": 0, "allow_edit": "Retreat Manager",
         "style": "Success"},
        {"state": "Cancelled", "doc_status": 0, "allow_edit": "Retreat Manager",
         "style": "Danger"},
        {"state": "No Show", "doc_status": 0, "allow_edit": "Retreat Manager",
         "style": "Inverse"},
    ]

    transitions = [
        {"state": "Pending", "action": "Confirm", "next_state": "Confirmed",
         "allowed": "Retreat Manager", "condition": "doc.retreat and doc.guest_name"},
        {"state": "Pending", "action": "Cancel", "next_state": "Cancelled",
         "allowed": "Retreat Manager"},
        {"state": "Confirmed", "action": "Check In", "next_state": "Checked In",
         "allowed": "Retreat Manager"},
        {"state": "Confirmed", "action": "Cancel", "next_state": "Cancelled",
         "allowed": "Retreat Manager"},
        {"state": "Confirmed", "action": "No Show", "next_state": "No Show",
         "allowed": "Retreat Manager"},
        {"state": "Checked In", "action": "Complete", "next_state": "Completed",
         "allowed": "Retreat Manager"},
    ]

    for s in states:
        workflow.append("states", s)
    for t in transitions:
        workflow.append("transitions", t)

    workflow.insert(ignore_permissions=True)


def create_expense_workflow():
    """Expense approval: Draft → Under Review → Approved → Submitted"""
    if frappe.db.exists("Workflow", "Retreat Expense Workflow"):
        return

    workflow = frappe.new_doc("Workflow")
    workflow.workflow_name = "Retreat Expense Workflow"
    workflow.document_type = "Retreat Expense"
    workflow.is_active = 1

    states = [
        {"state": "Draft", "doc_status": 0, "allow_edit": "Retreat Manager", "style": "Warning"},
        {"state": "Under Review", "doc_status": 0, "allow_edit": "Accounts User", "style": "Info"},
        {"state": "Approved", "doc_status": 0, "allow_edit": "Accounts Manager", "style": "Primary"},
        {"state": "Submitted", "doc_status": 1, "allow_edit": "Accounts Manager", "style": "Success"},
        {"state": "Rejected", "doc_status": 0, "allow_edit": "Accounts User", "style": "Danger"},
    ]

    transitions = [
        {"state": "Draft", "action": "Submit for Review", "next_state": "Under Review", "allowed": "Retreat Manager"},
        {"state": "Under Review", "action": "Approve", "next_state": "Approved", "allowed": "Accounts User",
         "condition": "doc.amount <= 10000000"},  # < 10M VND auto-approvable by Accounts User
        {"state": "Under Review", "action": "Approve", "next_state": "Approved", "allowed": "Accounts Manager"},
        {"state": "Under Review", "action": "Reject", "next_state": "Rejected", "allowed": "Accounts User"},
        {"state": "Approved", "action": "Submit", "next_state": "Submitted", "allowed": "Accounts Manager"},
        {"state": "Rejected", "action": "Revise", "next_state": "Draft", "allowed": "Retreat Manager"},
    ]

    for s in states:
        workflow.append("states", s)
    for t in transitions:
        workflow.append("transitions", t)

    workflow.insert(ignore_permissions=True)


def create_verification_workflow():
    """7-Layer Verification: Pending → In Progress → Inspected → Fully Verified"""
    if frappe.db.exists("Workflow", "Retreat Verification Workflow"):
        return

    workflow = frappe.new_doc("Workflow")
    workflow.workflow_name = "Retreat Verification Workflow"
    workflow.document_type = "Retreat"
    workflow.is_active = 1

    states = [
        {"state": "Draft", "doc_status": 0, "allow_edit": "Retreat Owner", "style": "Warning"},
        {"state": "Pending Verification", "doc_status": 0, "allow_edit": "Retreat Manager", "style": "Info"},
        {"state": "Identity Checked", "doc_status": 0, "allow_edit": "Retreat Manager", "style": "Info"},
        {"state": "Legal Checked", "doc_status": 0, "allow_edit": "Retreat Manager", "style": "Info"},
        {"state": "Inspection Scheduled", "doc_status": 0, "allow_edit": "Retreat Manager", "style": "Primary"},
        {"state": "Inspected", "doc_status": 0, "allow_edit": "Retreat Manager", "style": "Primary"},
        {"state": "Fully Verified", "doc_status": 0, "allow_edit": "Retreat Manager", "style": "Success"},
        {"state": "Rejected", "doc_status": 0, "allow_edit": "Retreat Manager", "style": "Danger"},
    ]

    transitions = [
        {"state": "Draft", "action": "Submit for Verification", "next_state": "Pending Verification", "allowed": "Retreat Owner"},
        {"state": "Pending Verification", "action": "Verify Identity", "next_state": "Identity Checked", "allowed": "Retreat Manager"},
        {"state": "Identity Checked", "action": "Verify Legal", "next_state": "Legal Checked", "allowed": "Retreat Manager"},
        {"state": "Legal Checked", "action": "Schedule Inspection", "next_state": "Inspection Scheduled", "allowed": "Retreat Manager"},
        {"state": "Inspection Scheduled", "action": "Confirm Inspection", "next_state": "Inspected", "allowed": "Retreat Manager"},
        {"state": "Inspected", "action": "Approve", "next_state": "Fully Verified", "allowed": "System Manager"},
        {"state": "Pending Verification", "action": "Reject", "next_state": "Rejected", "allowed": "Retreat Manager"},
        {"state": "Identity Checked", "action": "Reject", "next_state": "Rejected", "allowed": "Retreat Manager"},
        {"state": "Legal Checked", "action": "Reject", "next_state": "Rejected", "allowed": "Retreat Manager"},
        {"state": "Inspected", "action": "Reject", "next_state": "Rejected", "allowed": "System Manager"},
        {"state": "Rejected", "action": "Resubmit", "next_state": "Pending Verification", "allowed": "Retreat Owner"},
    ]

    for s in states:
        workflow.append("states", s)
    for t in transitions:
        workflow.append("transitions", t)

    workflow.insert(ignore_permissions=True)


def create_healer_onboarding_workflow():
    """Healer onboarding: Application → Review → Approved / Rejected"""
    if frappe.db.exists("Workflow", "Healer Onboarding Workflow"):
        return

    workflow = frappe.new_doc("Workflow")
    workflow.workflow_name = "Healer Onboarding Workflow"
    workflow.document_type = "Healer"
    workflow.is_active = 1

    states = [
        {"state": "Pending Approval", "doc_status": 0, "allow_edit": "Retreat Manager", "style": "Warning"},
        {"state": "Under Review", "doc_status": 0, "allow_edit": "Retreat Manager", "style": "Info"},
        {"state": "Active", "doc_status": 0, "allow_edit": "Retreat Manager", "style": "Success"},
        {"state": "Inactive", "doc_status": 0, "allow_edit": "Retreat Manager", "style": "Inverse"},
    ]

    transitions = [
        {"state": "Pending Approval", "action": "Review", "next_state": "Under Review",
         "allowed": "Retreat Manager"},
        {"state": "Under Review", "action": "Approve", "next_state": "Active",
         "allowed": "Retreat Manager", "condition": "doc.credentials"},
        {"state": "Under Review", "action": "Reject", "next_state": "Inactive",
         "allowed": "Retreat Manager"},
        {"state": "Active", "action": "Deactivate", "next_state": "Inactive",
         "allowed": "Retreat Manager"},
        {"state": "Inactive", "action": "Reactivate", "next_state": "Active",
         "allowed": "Retreat Manager"},
    ]

    for s in states:
        workflow.append("states", s)
    for t in transitions:
        workflow.append("transitions", t)

    workflow.insert(ignore_permissions=True)


def create_lead_workflow():
    """Lead pipeline: New → Contacted → Interested → Negotiating → Converted/Lost"""
    if frappe.db.exists("Workflow", "Retreat Lead Workflow"):
        return

    workflow = frappe.new_doc("Workflow")
    workflow.workflow_name = "Retreat Lead Workflow"
    workflow.document_type = "Retreat Lead"
    workflow.is_active = 1

    states = [
        {"state": "New", "doc_status": 0, "allow_edit": "Sales User", "style": "Primary"},
        {"state": "Contacted", "doc_status": 0, "allow_edit": "Sales User", "style": "Info"},
        {"state": "Interested", "doc_status": 0, "allow_edit": "Sales User", "style": "Info"},
        {"state": "Negotiating", "doc_status": 0, "allow_edit": "Sales User", "style": "Warning"},
        {"state": "Converted", "doc_status": 0, "allow_edit": "Sales User", "style": "Success"},
        {"state": "Lost", "doc_status": 0, "allow_edit": "Sales User", "style": "Danger"},
    ]

    transitions = [
        {"state": "New", "action": "Contact", "next_state": "Contacted", "allowed": "Sales User"},
        {"state": "Contacted", "action": "Mark Interested", "next_state": "Interested", "allowed": "Sales User"},
        {"state": "Contacted", "action": "Mark Lost", "next_state": "Lost", "allowed": "Sales User"},
        {"state": "Interested", "action": "Start Negotiation", "next_state": "Negotiating", "allowed": "Sales User"},
        {"state": "Interested", "action": "Mark Lost", "next_state": "Lost", "allowed": "Sales User"},
        {"state": "Negotiating", "action": "Convert", "next_state": "Converted", "allowed": "Sales User"},
        {"state": "Negotiating", "action": "Mark Lost", "next_state": "Lost", "allowed": "Sales User"},
        {"state": "Lost", "action": "Reopen", "next_state": "New", "allowed": "Sales User"},
    ]

    for s in states:
        workflow.append("states", s)
    for t in transitions:
        workflow.append("transitions", t)

    workflow.insert(ignore_permissions=True)
