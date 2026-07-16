import datetime
from zoneinfo import ZoneInfo

from django.test import SimpleTestCase

from core.services import schedule

UTC = ZoneInfo('UTC')


class DrawScheduleTests(SimpleTestCase):
    def test_next_draw_during_est_is_5am_utc(self):
        # 2026-01-15 12:00 UTC = 07:00 EST (UTC-5, winter)
        now = datetime.datetime(2026, 1, 15, 12, 0, tzinfo=UTC)
        next_draw = schedule.next_draw_at_utc(now)
        self.assertEqual(next_draw, datetime.datetime(2026, 1, 16, 5, 0, tzinfo=UTC))

    def test_next_draw_during_edt_is_4am_utc(self):
        # 2026-07-15 12:00 UTC = 08:00 EDT (UTC-4, summer)
        now = datetime.datetime(2026, 7, 15, 12, 0, tzinfo=UTC)
        next_draw = schedule.next_draw_at_utc(now)
        self.assertEqual(next_draw, datetime.datetime(2026, 7, 16, 4, 0, tzinfo=UTC))

    def test_current_draw_date_matches_next_draw_date(self):
        now = datetime.datetime(2026, 3, 1, 18, 0, tzinfo=UTC)
        self.assertEqual(schedule.current_draw_date(now), schedule.next_draw_at_utc(now).date())

    def test_spring_forward_dst_transition(self):
        # US DST starts 2026-03-08 at 02:00 local (EST -> EDT). A drawing
        # requested from just before the jump should still land on exactly
        # midnight ET of the following day once converted to UTC.
        before_jump = datetime.datetime(2026, 3, 7, 10, 0, tzinfo=UTC)  # 05:00 EST
        next_draw = schedule.next_draw_at_utc(before_jump)
        # 2026-03-08 00:00 EST would be UTC-5, but the draw date requested
        # (2026-03-08) is itself already on EST since the jump happens later
        # that day at 02:00 local -- so midnight is still UTC-5.
        self.assertEqual(next_draw, datetime.datetime(2026, 3, 8, 5, 0, tzinfo=UTC))

    def test_fall_back_dst_transition(self):
        # US DST ends 2026-11-01. A request the day before should compute
        # midnight ET of 2026-11-01, which is still EDT (UTC-4) since the
        # fall-back happens later that day at 02:00 local.
        before_fallback = datetime.datetime(2026, 10, 31, 10, 0, tzinfo=UTC)  # 06:00 EDT
        next_draw = schedule.next_draw_at_utc(before_fallback)
        self.assertEqual(next_draw, datetime.datetime(2026, 11, 1, 4, 0, tzinfo=UTC))

    def test_snapshot_cutoff_is_2350_et_the_eve_of_draw(self):
        draw_date = datetime.date(2026, 7, 16)
        cutoff = schedule.snapshot_cutoff_et(draw_date)
        self.assertEqual(cutoff.date(), datetime.date(2026, 7, 15))
        self.assertEqual((cutoff.hour, cutoff.minute), (23, 50))

    def test_commit_time_is_0001_et_the_eve_of_draw(self):
        draw_date = datetime.date(2026, 7, 16)
        commit_time = schedule.commit_at_et(draw_date)
        self.assertEqual(commit_time.date(), datetime.date(2026, 7, 15))
        self.assertEqual((commit_time.hour, commit_time.minute), (0, 1))
