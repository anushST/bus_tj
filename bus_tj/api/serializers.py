"""Serializators for api."""
from rest_framework.serializers import ModelSerializer

from tracker.models import BusStop, Vehicle


class VehicleSerializer(ModelSerializer):
    """Vehicle model serializer."""

    class Meta:
        """Meta-datas."""

        model = Vehicle
        fields = ('name',)


class StopSerializer(ModelSerializer):
    """BusStop model serializer."""

    class Meta:
        """Meta-datas."""

        model = BusStop
        fields = ('id', 'name')
