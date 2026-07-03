from django.urls import path

from .views import EventIngestView, ManagerStatsView

urlpatterns = [
    path("events/", EventIngestView.as_view(), name="event-ingest"),
    path("manage/stats/", ManagerStatsView.as_view(), name="manager-stats"),
]
