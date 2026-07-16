"""America/New_York drawing schedule helpers. zoneinfo handles DST
transitions automatically -- "midnight ET" is always the correct wall-clock
midnight regardless of EST/EDT.
"""
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from django.utils import timezone

ET = ZoneInfo('America/New_York')


def now_et() -> datetime:
    return timezone.now().astimezone(ET)


def current_draw_date(now=None):
    """The ET calendar date of "tonight's" drawing: it fires at 00:00 ET
    marking the start of the day *after* today, so e.g. all of Tuesday
    (ET) counts down to the drawing dated Wednesday.
    """
    moment = (now or timezone.now()).astimezone(ET)
    return moment.date() + timedelta(days=1)


def next_draw_at_utc(now=None):
    draw_date = current_draw_date(now)
    next_midnight_et = datetime.combine(draw_date, time(0, 0), tzinfo=ET)
    return next_midnight_et.astimezone(ZoneInfo('UTC'))


def commit_at_et(draw_date):
    """00:01 ET on the eve of `draw_date`'s midnight opening."""
    return datetime.combine(draw_date - timedelta(days=1), time(0, 1), tzinfo=ET)


def snapshot_cutoff_et(draw_date):
    """23:50 ET on the eve of `draw_date`'s midnight opening."""
    return datetime.combine(draw_date - timedelta(days=1), time(23, 50), tzinfo=ET)
