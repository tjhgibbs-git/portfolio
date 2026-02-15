import uuid
import json
from django.db import models
from django.conf import settings


class MeetupSession(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='meetup_sessions',
    )
    meeting_time = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Meetup {self.uuid} ({self.created_at:%Y-%m-%d %H:%M})"


class Person(models.Model):
    session = models.ForeignKey(
        MeetupSession,
        on_delete=models.CASCADE,
        related_name='people',
    )
    name = models.CharField(max_length=100)
    origin_label = models.CharField(max_length=255)
    origin_lat = models.FloatField()
    origin_lon = models.FloatField()
    home_label = models.CharField(max_length=255)
    home_lat = models.FloatField()
    home_lon = models.FloatField()

    class Meta:
        verbose_name_plural = 'people'

    def __str__(self):
        return f"{self.name} (from {self.origin_label})"


class MeetupResult(models.Model):
    session = models.ForeignKey(
        MeetupSession,
        on_delete=models.CASCADE,
        related_name='results',
    )
    station_name = models.CharField(max_length=200)
    station_lat = models.FloatField()
    station_lon = models.FloatField()
    score_fairness = models.FloatField(null=True)
    score_efficiency = models.FloatField(null=True)
    score_quick_arrival = models.FloatField(null=True)
    score_easy_home = models.FloatField(null=True)
    journey_details_json = models.TextField(default='{}')
    google_maps_url = models.URLField(max_length=500)

    class Meta:
        ordering = ['score_fairness']

    def __str__(self):
        return f"{self.station_name} (fairness: {self.score_fairness})"

    @property
    def journey_details(self):
        return json.loads(self.journey_details_json)

    @journey_details.setter
    def journey_details(self, value):
        self.journey_details_json = json.dumps(value)
