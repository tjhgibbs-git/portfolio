from django.urls import path
from . import views

app_name = 'tools'

urlpatterns = [
    path('', views.ToolListView.as_view(), name='list'),
    path('<slug:slug>/', views.tool_detail, name='detail'),
    path('preview/<slug:slug>/', views.tool_preview, name='preview'),
]