from datetime import datetime, time
from decimal import Decimal
from zoneinfo import ZoneInfo

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.futsals.models import Court, Futsal

from .models import PriceRule
from .services import resolve_price
from .utils import WEEKENDS, mask_from_days

User = get_user_model()
KTM = ZoneInfo("Asia/Kathmandu")


class PriceResolutionTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(email="o@example.com", phone="9811111111", password="x")
        self.futsal = Futsal.objects.create(name="F", created_by=self.owner,
                                             status=Futsal.Status.ACTIVE, timezone="Asia/Kathmandu")
        self.court = Court.objects.create(futsal=self.futsal, name="C", default_price=Decimal("800"))

    def _rule(self, name, start, end, price, priority=0, days=None):
        return PriceRule.objects.create(
            court=self.court, name=name, start_time=time(start), end_time=time(end),
            price=Decimal(price), priority=priority,
            days_mask=mask_from_days(days) if days is not None else 0b1111111,
        )

    def test_falls_back_to_default_when_no_rule(self):
        when = datetime(2026, 6, 22, 10, 0, tzinfo=KTM)  # Monday 10:00
        self.assertEqual(resolve_price(self.court, when), Decimal("800"))

    def test_night_bracket_applies(self):
        self._rule("Night", 18, 22, "1500")
        when = datetime(2026, 6, 22, 19, 0, tzinfo=KTM)  # Mon 19:00
        self.assertEqual(resolve_price(self.court, when), Decimal("1500"))

    def test_priority_wins_on_overlap(self):
        self._rule("Base evening", 17, 23, "1200", priority=0)
        self._rule("Weekend surge", 17, 23, "2000", priority=10, days=[5, 6])
        sat = datetime(2026, 6, 27, 20, 0, tzinfo=KTM)  # Saturday
        mon = datetime(2026, 6, 22, 20, 0, tzinfo=KTM)  # Monday
        self.assertEqual(resolve_price(self.court, sat), Decimal("2000"))  # surge
        self.assertEqual(resolve_price(self.court, mon), Decimal("1200"))  # base

    def test_utc_input_converted_to_venue_local(self):
        self._rule("Morning", 6, 10, "600")
        # 01:30 UTC == 07:15 NPT (UTC+5:45) -> morning bracket
        when = datetime(2026, 6, 22, 1, 30, tzinfo=ZoneInfo("UTC"))
        self.assertEqual(resolve_price(self.court, when), Decimal("600"))


class QuoteEndpointTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(email="o@example.com", phone="9811111111", password="x")
        self.futsal = Futsal.objects.create(name="F", created_by=self.owner,
                                             status=Futsal.Status.ACTIVE)
        self.court = Court.objects.create(futsal=self.futsal, name="C", default_price=Decimal("800"))
        PriceRule.objects.create(court=self.court, name="Night", start_time=time(18),
                                 end_time=time(22), price=Decimal("1500"))

    def test_quote_is_public_and_authoritative(self):
        res = self.client.get(reverse("price-quote"),
                              {"court": str(self.court.pk), "start": "2026-06-22T19:00:00+05:45"})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(Decimal(res.data["price"]), Decimal("1500"))
        self.assertEqual(res.data["currency"], "NPR")
