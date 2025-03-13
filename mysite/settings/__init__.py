"""
Settings package initialization.
This file determines which settings file to use based on DJANGO_SETTINGS_MODULE environment variable.
"""
import os

# Default to development settings if DJANGO_SETTINGS_MODULE is not set
settings_module = os.environ.get('DJANGO_SETTINGS_MODULE', 'mysite.settings.development')

# If directly importing from settings, use the specified module
if settings_module == 'mysite.settings':
    from .development import *