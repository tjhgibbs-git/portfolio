# mysite/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from main import views as main_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('projects/', main_views.portfolio, name='portfolio'),
    path('projects/<slug:slug>/', main_views.project_detail, name='project_detail'),
    path('tools/', include('tools.urls')),
    path('recipes/', include('recipes.urls')),
    path('meetup/', include('meetup.urls')),
    path('', include('blog.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)