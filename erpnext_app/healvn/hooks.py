app_name = "healvn"
app_title = "HealVN"
app_publisher = "HealVN Team"
app_description = "Vietnam's Healing Tourism Platform — Full ERPNext Business Management"
app_email = "hello@healvn.com"
app_license = "MIT"
app_version = "2.0.0"

# Required Apps
required_apps = ["frappe", "erpnext"]

# ---------- DocType Events ----------
doc_events = {
    "Sales Order": {
        "on_submit": "healvn.healvn.doctype.retreat_booking.retreat_booking.on_sales_order_submit",
        "on_cancel": "healvn.healvn.doctype.retreat_booking.retreat_booking.on_sales_order_cancel",
    },
    "Sales Invoice": {
        "on_submit": "healvn.healvn.utils.notify_booking_payment",
    },
}

# ---------- Scheduled Tasks ----------
scheduler_events = {
    "daily": [
        "healvn.healvn.tasks.send_checkin_reminders",
        "healvn.healvn.tasks.update_retreat_ratings",
        "healvn.healvn.tasks.expire_pending_bookings",
    ],
    "weekly": [
        "healvn.healvn.tasks.generate_wellness_reports",
        "healvn.healvn.tasks.sync_retreat_availability",
    ],
    "monthly": [
        "healvn.healvn.tasks.send_partner_reports",
    ],
}

# ---------- Web Routes ----------
website_route_rules = [
    {"from_route": "/retreats", "to_route": "Retreat"},
    {"from_route": "/retreats/<path:name>", "to_route": "Retreat"},
    {"from_route": "/bookings", "to_route": "Retreat Booking"},
    {"from_route": "/healers", "to_route": "Healer"},
    {"from_route": "/packages", "to_route": "Retreat Package"},
    {"from_route": "/packages/<path:name>", "to_route": "Retreat Package"},
]

# ---------- Jinja Filters ----------
jinja = {
    "methods": [
        "healvn.healvn.utils.format_currency_vnd",
        "healvn.healvn.utils.get_retreat_thumbnail",
    ],
}

# ---------- Fixtures (export/import data) ----------
fixtures = [
    {"dt": "Custom Field", "filters": [["module", "=", "HealVN"]]},
    {"dt": "Property Setter", "filters": [["module", "=", "HealVN"]]},
    {"dt": "Workspace", "filters": [["module", "=", "HealVN"]]},
    {"dt": "Workflow", "filters": [["name", "like", "Retreat%"]]},
    {"dt": "Workflow", "filters": [["name", "like", "Healer%"]]},
    {"dt": "Print Format", "filters": [["name", "like", "HealVN%"]]},
    {"dt": "Role", "filters": [["name", "in", ["Retreat Manager", "Retreat Owner", "Healer", "Wellness Advisor"]]]},
]

# ---------- Portal Menu Items ----------
portal_menu_items = [
    {"title": "My Retreats", "route": "/retreats", "role": "Retreat Owner"},
    {"title": "My Bookings", "route": "/bookings", "role": "Customer"},
    {"title": "Packages", "route": "/packages", "role": ""},
]

# ---------- Setup ----------
setup_wizard_requires = "assets/healvn/js/setup_wizard.js"
after_install = "healvn.healvn.setup.after_install"
after_migrate = "healvn.healvn.setup.after_install"

# ─── Boot Session (inject HealVN config into client) ───
boot_session = "healvn.healvn.boot.boot_session"

# ─── Override Standard DocTypes (add HealVN tabs) ──────
override_doctype_class = {}

# ─── Standard Queries ─────────────────────────────────
override_whitelisted_methods = {}

# ─── User Permissions ─────────────────────────────────
has_permission = {}

# ─── Dashboard Config ─────────────────────────────────
# Add booking count to Customer dashboard, etc.
override_doctype_dashboards = {
    "Customer": "healvn.healvn.dashboard_overrides.customer_dashboard",
    "Supplier": "healvn.healvn.dashboard_overrides.supplier_dashboard",
}

# ─── Notification Config ──────────────────────────────
notification_config = "healvn.healvn.notifications.get_notification_config"
