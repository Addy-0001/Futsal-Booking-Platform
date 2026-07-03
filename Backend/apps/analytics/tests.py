from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import EventLog


class AnalyticsTests(APITestCase):
    def test_anonymous_event_ingest(self):
        res = self.client.post(reverse("event-ingest"),
                               {"name": "page_view", "path": "/futsals", "session_id": "s1",
                                "props": {"ref": "home"}}, format="json")
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        ev = EventLog.objects.get()
        self.assertEqual(ev.name, "page_view")
        self.assertEqual(ev.props["ref"], "home")
        self.assertIsNone(ev.user)

    def test_name_required(self):
        res = self.client.post(reverse("event-ingest"), {"path": "/x"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
