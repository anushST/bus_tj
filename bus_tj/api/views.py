"""All APIs are here."""
from geopy.distance import geodesic
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from rest_framework import status

from tracker.models import BusStop, Path, Vehicle


def calculate_distance(bus_id, stop_id) -> int:
    """Calculate distance between bus and stop."""
    bus = Vehicle.objects.get(pk=bus_id)
    stop = BusStop.objects.get(pk=stop_id)
    bus_path = Path.objects.get(location=bus.location)
    stop_path = Path.objects.get(location=stop.location)
    return stop_path.distance - bus_path.distance


class LocationViewSet(ViewSet):
    """Get location of the bus."""

    def list(self, request):
        """Get location of the bus."""
        bus_id = request.GET.get('bus')
        stop_id = request.GET.get('stop')
        return Response({'distance': calculate_distance(bus_id, stop_id)})


class BusViewSet(ViewSet):
    """Get buses which pass the stop."""

    def list(self, request):
        """Get buses which pass the stop."""
        stop_id = request.GET.get('stop')
        stop = BusStop.objects.get(pk=int(stop_id))
        buses = stop.buses.all()
        response = {'buses': [[i.name, i.id] for i in buses]}
        return Response(response, status=status.HTTP_200_OK)


class StopViewSet(ViewSet):
    """Get 4 bus_stops near you."""

    def list(self, request):
        """Get 4 bus_stops near you."""
        latitude = request.GET.get('latitude')
        longitude = request.GET.get('longitude')
        if latitude is None or longitude is None:
            return Response({'message': 'params are required'})
        our_location = (latitude, longitude)
        queryset = BusStop.objects.all()
        distances = {}
        for stop in queryset:
            point = (stop.location.latitude, stop.location.longitude)
            distance = geodesic(our_location, point).meters
            distances[distance] = stop
        keys = sorted(distances.keys())[:4]
        response = {
            'stops': [[distances[key].name, distances[key].id] for key in keys]
        }
        return Response(response, status=status.HTTP_200_OK)
