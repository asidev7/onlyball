"""Round lifecycle helpers."""

from __future__ import annotations

from datetime import timedelta
from django.utils import timezone

from ..models import Round


def _next_midnight_utc():
    now = timezone.now()
    tomorrow = (now + timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    return tomorrow


def get_or_create_current_round() -> Round:
    """Return the open round, creating round #1 (drawing at next UTC midnight)
    if none exists yet."""
    rnd = Round.objects.filter(status=Round.OPEN).order_by("-index").first()
    if rnd:
        return rnd
    last = Round.objects.order_by("-index").first()
    index = (last.index + 1) if last else 1
    return Round.objects.create(
        index=index,
        draws_at=_next_midnight_utc(),
        status=Round.OPEN,
    )
