"""Constants."""
DOMAIN = "radon_monitor"
DEFAULTS = {
    "warning": 100.0, "high": 200.0, "recovery": 80.0,
    "delay_hours": 2.0, "recovery_hours": 6.0,
    "problem_hours": 2.0, "stale_hours": 3.0,
    "notification_service": "persistent_notification.create",
}
