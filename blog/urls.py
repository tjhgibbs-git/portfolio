from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
    path('', views.post_list, name='post_list'),
    path('tag/<slug:tag_slug>/', views.post_list, name='posts_by_tag'),
    path('<slug:slug>/', views.post_detail, name='post_detail'),
]