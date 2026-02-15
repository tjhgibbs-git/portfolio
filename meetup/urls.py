from django.urls import path
from . import views

app_name = 'meetup'

urlpatterns = [
    path('', views.index, name='index'),
    path('calculate/', views.calculate, name='calculate'),
    path('results/<uuid:session_uuid>/', views.results, name='results'),
    path('api/autocomplete/', views.autocomplete, name='autocomplete'),
]
