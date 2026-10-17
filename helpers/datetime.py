from flask import Blueprint, request, redirect, url_for, flash, current_app as app
from datetime import datetime, date, time
import zoneinfo
bp = Blueprint('app', __name__)

def combine_date_time(date_str: str, time_str: str, tz: str | None = None) -> datetime:
    try:
        d: date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValueError(f"Invalid date format {date_str!r}: {exc}")

    try:
        t: time = datetime.strptime(time_str, "%H:%M:%S.%f").time()
    except ValueError:
        try:
            t = datetime.strptime(time_str, "%H:%M:%S").time()
        except ValueError:
            t = datetime.strptime(time_str, "%H:%M").time()

    combined = datetime.combine(d, t)

    if tz:
        tzinfo = zoneinfo.ZoneInfo(tz)
        combined = combined.replace(tzinfo=tzinfo)

    return combined
