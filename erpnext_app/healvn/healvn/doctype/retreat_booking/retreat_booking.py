# Copyright (c) 2025, HealVN Team and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt, nowdate, getdate, add_days, date_diff, fmt_money
from frappe import _


class RetreatBooking(Document):
    """
    DocType: Retreat Booking
    Represents a guest's booking at a wellness retreat.
    Auto-creates Sales Order (on confirm) and Sales Invoice (on checkout).
    """

    def validate(self):
        self.validate_dates()
        self.validate_availability()
        self.calculate_totals()

    def before_insert(self):
        if not self.booking_id:
            self.booking_id = frappe.generate_hash(length=10).upper()

    def on_update(self):
        if self.has_value_changed("status"):
            self.handle_status_change()

    def on_trash(self):
        if self.status in ("Confirmed", "Checked In"):
            frappe.throw(_("Cannot delete a confirmed or active booking. Cancel it first."))

    # ─── Validation ──────────────────────────────────────────

    def validate_dates(self):
        if not self.check_in or not self.check_out:
            frappe.throw(_("Check-in and Check-out dates are required"))

        check_in = getdate(self.check_in)
        check_out = getdate(self.check_out)

        if check_in >= check_out:
            frappe.throw(_("Check-out must be after Check-in"))
        if check_in < getdate(nowdate()) and self.is_new():
            frappe.throw(_("Check-in date cannot be in the past"))

        self.duration_nights = date_diff(check_out, check_in)

    def validate_availability(self):
        if not self.retreat:
            return
        retreat = frappe.get_doc("Retreat", self.retreat)
        avail = retreat.check_availability(self.check_in, self.check_out)
        if not avail["available"]:
            frappe.throw(
                _("No availability at {0} for {1} to {2}. Max capacity: {3}")
                .format(retreat.retreat_name, self.check_in, self.check_out, avail["max_guests"])
            )

    def calculate_totals(self):
        if not self.retreat:
            return
        retreat = frappe.get_doc("Retreat", self.retreat)

        if retreat.price_per_package and retreat.package_duration_days:
            self.subtotal = flt(retreat.price_per_package)
            self.pricing_type = "Package"
        elif retreat.price_per_night:
            self.subtotal = flt(retreat.price_per_night * self.duration_nights * (self.num_guests or 1))
            self.pricing_type = "Per Night"
        else:
            self.subtotal = 0

        self.tax_amount = flt(self.subtotal * flt(self.tax_rate or 0) / 100, 2)
        self.discount_amount = flt(self.discount_amount or 0, 2)
        self.total_amount = flt(self.subtotal + self.tax_amount - self.discount_amount, 2)

    # ─── Status Workflow ──────────────────────────────────────

    def handle_status_change(self):
        if self.status == "Confirmed":
            self.create_sales_order()
            self.send_confirmation_email()
        elif self.status == "Checked In":
            self.actual_check_in = nowdate()
        elif self.status == "Completed":
            self.actual_check_out = nowdate()
            self.create_sales_invoice()
            self.request_review()
        elif self.status == "Cancelled":
            self.cancel_linked_orders()
            self.process_refund()

    # ─── ERPNext Sales Order ──────────────────────────────────

    def create_sales_order(self):
        """Auto-create Sales Order on booking confirmation"""
        if self.sales_order:
            return

        retreat = frappe.get_doc("Retreat", self.retreat)
        if not retreat.item_code:
            frappe.throw(_("Retreat {0} has no linked Item. Please save the retreat first.").format(self.retreat))

        customer = self.get_or_create_customer()

        so = frappe.new_doc("Sales Order")
        so.customer = customer
        so.delivery_date = self.check_in
        so.po_no = self.booking_id
        so.company = frappe.defaults.get_user_default("Company")

        so.append("items", {
            "item_code": retreat.item_code,
            "qty": self.num_guests or 1,
            "rate": self.subtotal / (self.num_guests or 1),
            "delivery_date": self.check_in,
            "description": (
                f"Retreat Booking: {retreat.retreat_name}\n"
                f"Check-in: {self.check_in} | Check-out: {self.check_out}\n"
                f"Guests: {self.num_guests or 1} | Nights: {self.duration_nights}"
            ),
        })

        so.insert(ignore_permissions=True)
        so.submit()
        self.db_set("sales_order", so.name)

        frappe.msgprint(
            _("Sales Order {0} created").format(
                frappe.utils.get_link_to_form("Sales Order", so.name)
            ),
            alert=True,
        )

    def create_sales_invoice(self):
        """Create Sales Invoice on checkout/completion"""
        if self.sales_invoice:
            return
        if not self.sales_order:
            return

        from erpnext.selling.doctype.sales_order.sales_order import make_sales_invoice
        si = make_sales_invoice(self.sales_order)
        si.insert(ignore_permissions=True)
        si.submit()
        self.db_set("sales_invoice", si.name)
        self.db_set("payment_status", "Invoiced")

    # ─── Customer ─────────────────────────────────────────────

    def get_or_create_customer(self):
        """Get existing customer or create new one from guest info"""
        if self.customer:
            return self.customer

        # Try to find by email
        if self.guest_email:
            existing = frappe.db.get_value("Customer", {"email_id": self.guest_email})
            if existing:
                self.db_set("customer", existing)
                return existing

        # Create new customer
        customer = frappe.new_doc("Customer")
        customer.customer_name = self.guest_name or "Walk-in Guest"
        customer.customer_type = "Individual"
        customer.customer_group = "Individual"
        customer.territory = "Vietnam"
        customer.email_id = self.guest_email
        customer.mobile_no = self.guest_phone
        customer.insert(ignore_permissions=True)
        self.db_set("customer", customer.name)
        return customer.name

    # ─── Notifications ────────────────────────────────────────

    def send_confirmation_email(self):
        if not self.guest_email:
            return
        retreat = frappe.get_doc("Retreat", self.retreat)
        frappe.sendmail(
            recipients=[self.guest_email],
            subject=f"🌿 Booking Confirmed — {retreat.retreat_name}",
            message=frappe.render_template(
                "healvn/templates/emails/booking_confirmed.html",
                {"doc": self, "retreat": retreat},
            ),
        )

    def request_review(self):
        """Send review request email after checkout"""
        if not self.guest_email:
            return
        frappe.sendmail(
            recipients=[self.guest_email],
            subject="🌿 How was your wellness journey? Leave a review!",
            message=frappe.render_template(
                "healvn/templates/emails/review_request.html",
                {"doc": self},
            ),
        )

    def cancel_linked_orders(self):
        """Cancel linked Sales Order if booking is cancelled"""
        if self.sales_order and frappe.db.get_value("Sales Order", self.sales_order, "docstatus") == 1:
            so = frappe.get_doc("Sales Order", self.sales_order)
            so.cancel()

    def process_refund(self):
        """Handle refund logic based on cancellation policy"""
        if not self.sales_invoice:
            return
        # Refund logic goes here — depends on cancellation policy
        self.db_set("payment_status", "Refund Pending")

    # ─── API Helper ───────────────────────────────────────────

    def as_booking_dict(self):
        return {
            "booking_id": self.booking_id,
            "retreat": self.retreat,
            "retreat_name": frappe.db.get_value("Retreat", self.retreat, "retreat_name"),
            "guest_name": self.guest_name,
            "check_in": str(self.check_in),
            "check_out": str(self.check_out),
            "num_guests": self.num_guests,
            "duration_nights": self.duration_nights,
            "total_amount": self.total_amount,
            "status": self.status,
            "payment_status": self.payment_status,
        }


# ─── DocEvent Handlers ──────────────────────────────────────

def on_sales_order_submit(doc, method):
    """Called when Sales Order linked to a booking is submitted"""
    booking = frappe.db.get_value(
        "Retreat Booking", {"sales_order": doc.name}, "name"
    )
    if booking:
        frappe.db.set_value("Retreat Booking", booking, "payment_status", "Order Created")


def on_sales_order_cancel(doc, method):
    """Called when Sales Order linked to a booking is cancelled"""
    booking = frappe.db.get_value(
        "Retreat Booking", {"sales_order": doc.name}, "name"
    )
    if booking:
        frappe.db.set_value("Retreat Booking", booking, {
            "status": "Cancelled",
            "payment_status": "Cancelled",
        })
