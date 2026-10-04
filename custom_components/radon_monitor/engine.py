"""Radon calculations independent of Home Assistant."""
from calendar import monthrange
from datetime import datetime, timedelta
import math

PERIODS = {"7_days": 7, "30_days": 30, "6_months": 6, "1_year": 12, "2_years": 24}


def concentration(value, unit):
    """Normalize supported concentrations; missing/negative values are not zero."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number) or number < 0:
        return None
    if unit in ("Bq/m³", "Bq/m3"):
        return number
    if unit == "pCi/L":
        return number * 37
    return None


def window_start(now, key):
    """Use calendar months and years, including leap years."""
    if key in ("7_days", "30_days"):
        return now - timedelta(days=PERIODS[key])
    index = now.year * 12 + now.month - 1 - PERIODS[key]
    year, month = divmod(index, 12)
    month += 1
    return now.replace(year=year, month=month, day=min(now.day, monthrange(year, month)[1]))


def average(rows, start, end):
    """Average hourly means, weighted by overlap with the requested window.

    Coverage describes populated hourly buckets, not proof of continuous device
    sampling within each hour. Recorder does not expose that guarantee here.
    """
    weighted = seconds = 0.0
    oldest = None
    seen = set()
    for row in rows:
        stamp = float(row["start"])
        if stamp in seen:
            continue
        seen.add(stamp)
        value = concentration(row.get("mean"), "Bq/m³")
        if value is None:
            continue
        left = max(stamp, start.timestamp())
        right = min(stamp + 3600, end.timestamp())
        duration = max(0, right - left)
        if duration:
            weighted += value * duration
            seconds += duration
            oldest = left if oldest is None else min(oldest, left)
    total = (end - start).total_seconds()
    return {
        "value": round(weighted / seconds, 2) if seconds else None,
        "recorded_hours": round(seconds / 3600, 2),
        "bucket_coverage_percent": round(100 * seconds / total, 2) if total else 0,
        "partial": seconds < total * 0.99,
        "oldest_bucket": datetime.fromtimestamp(oldest, start.tzinfo).isoformat() if oldest else None,
    }


def weekly_trend(rows, now):
    """Compare adjacent seven-day averages only with adequate bucket coverage."""
    end_previous = now - timedelta(days=7)
    current = average(rows, end_previous, now)
    previous = average(rows, now - timedelta(days=14), end_previous)
    result = {"direction": "unavailable", "change": None,
              "previous_average": previous["value"]}
    if current["partial"] or previous["partial"] or current["value"] is None or previous["value"] is None:
        return result
    change = round(current["value"] - previous["value"], 2)
    result.update(direction="rising" if change > 0 else "falling" if change < 0 else "steady", change=change)
    return result


class AlertState:
    """Independent sustained thresholds; invalid data breaks concentration timers."""
    def __init__(self, saved=None):
        self.data = saved or {"since": {}, "alert": "normal", "problem_notified": False}

    def update(self, now, value, settings):
        since = self.data["since"]
        tests = {
            "elevated": value is not None and value >= settings["warning"],
            "high": value is not None and value >= settings["high"],
            "recovery": value is not None and value < settings["recovery"],
            "problem": value is None,
        }
        for key, active in tests.items():
            if active:
                since.setdefault(key, now)
            else:
                since.pop(key, None)
        def elapsed(key, hours):
            return key in since and now - since[key] >= hours * 3600
        messages = []
        if elapsed("problem", settings["problem_hours"]) and not self.data["problem_notified"]:
            self.data["problem_notified"] = True
            messages.append("sensor_problem")
        elif value is not None and self.data["problem_notified"]:
            self.data["problem_notified"] = False
            messages.append("sensor_restored")
        alert = self.data["alert"]
        if elapsed("high", settings["delay_hours"]) and alert != "high":
            self.data["alert"] = "high"
            messages.append("high")
        elif elapsed("elevated", settings["delay_hours"]) and alert == "normal":
            self.data["alert"] = "elevated"
            messages.append("elevated")
        elif elapsed("recovery", settings["recovery_hours"]) and alert != "normal":
            self.data["alert"] = "normal"
            messages.append("recovered")
        status = "sensor_problem" if value is None else (
            "high" if value >= settings["high"] else
            "elevated" if value >= settings["warning"] else
            "watch" if value >= settings["recovery"] else "normal")
        return status, messages
