from django.contrib import admin
from .models import MeetupSession, Person, MeetupResult


class PersonInline(admin.TabularInline):
    model = Person
    extra = 0


class MeetupResultInline(admin.TabularInline):
    model = MeetupResult
    extra = 0
    readonly_fields = ('station_name', 'score_fairness', 'score_efficiency',
                       'score_quick_arrival', 'score_easy_home', 'google_maps_url')


@admin.register(MeetupSession)
class MeetupSessionAdmin(admin.ModelAdmin):
    list_display = ('uuid', 'user', 'created_at', 'person_count')
    list_filter = ('created_at',)
    readonly_fields = ('uuid', 'created_at')
    inlines = [PersonInline, MeetupResultInline]

    def person_count(self, obj):
        return obj.people.count()
    person_count.short_description = 'People'


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ('name', 'session', 'origin_label', 'home_label')
    list_filter = ('session',)


@admin.register(MeetupResult)
class MeetupResultAdmin(admin.ModelAdmin):
    list_display = ('station_name', 'session', 'score_fairness',
                    'score_efficiency')
    list_filter = ('session',)
