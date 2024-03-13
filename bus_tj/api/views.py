"""All APIs are here."""
from geopy.distance import geodesic
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from rest_framework import status

from tracker.models import BusStop, Path, Location, Vehicle
from .exceptions import ObjectDoesNotExistError


def calculate_distance(bus_id: int, stop_id: int) -> int:
    """Calculate distance between bus and stop.

    Args:
        bus_id (int): PrimaryKey of the bus.
        stop_id (int): PrimaryKey of the stop.

    Raises:
        ObjectDoesNotExistError if can't find any object in models BusStop,
    Path and Vehicle.
        TypeError if Path.distance is not integer (sometimes it will work if
    it is not integer, but it is recommended to be integer).
    """
    try:
        bus = Vehicle.objects.get(pk=bus_id)
        stop = BusStop.objects.get(pk=stop_id)
        bus_path = Path.objects.get(location=bus.location)
        stop_path = Path.objects.get(location=stop.location)
        return stop_path.distance - bus_path.distance
    except Vehicle.DoesNotExist:
        raise ObjectDoesNotExistError('Vehicle object does not exist.')
    except BusStop.DoesNotExist:
        raise ObjectDoesNotExistError('BusStop object does not exist.')
    except Path.DoesNotExist:
        raise ObjectDoesNotExistError('Path object does not exist.')
    except TypeError:
        raise TypeError('Path.distance is not int (sometimes it will work if '
                        'it is not integer, but it is recommended to be '
                        'integer).')


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

    def retrieve(self, request, pk=None):
        """Get bus info."""
        bus = Vehicle.objects.get(pk=pk)
        return Response({'id': bus.id, 'name': bus.name},
                        status=status.HTTP_200_OK)

    def update(self, request, pk=None):
        """Update bus location."""
        data = request.data.json()
        latitude = data['latitude']
        longitude = data['longitude']
        if latitude is None or longitude is None:
            return Response({'message': 'params are required'})
        our_location = (latitude, longitude)
        queryset = Location.objects.all()
        distances = {}
        for location in queryset:
            point = (location.latitude, location.longitude)
            distance = geodesic(our_location, point).meters
            distances[distance] = location
        nearest_point = distances[sorted(distances.keys())[0]]
        bus = Vehicle.objects.get(pk=pk)
        bus.objects.update(location=nearest_point)
        return Response({}, status=status.HTTP_200_OK)


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

    def retrieve(self, request, pk=None):
        """Get stop info."""
        stop = BusStop.objects.get(pk=pk)
        return Response({'id': stop.id, 'name': stop.name},
                        status=status.HTTP_200_OK)
