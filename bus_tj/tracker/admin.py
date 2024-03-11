"""Admin-space settings."""
from django.contrib import admin

from .models import (
    BusStop, Location, Path, Vehicle)

admin.site.register(
    [BusStop, Location, Path, Vehicle,])
