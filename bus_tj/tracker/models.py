"""Models of the project."""
from django.db import models


class Location(models.Model):
    """Location model.

    Attributes:
    latitude (FloatField): The latitude of a point.
    longitude (FloatField): The longitude of a point.
    """

    latitude = models.FloatField()
    longitude = models.FloatField()


class Path(models.Model):
    """Path model.

    Attrivutes:
    path_id (IntegerField): The id of path.
    location (Location): The location of point.
    order (IntegerField): The order of point.
    distance (IntegerField): The distance from start point.
    """

    path_id = models.IntegerField()
    location = models.ForeignKey(
        Location, on_delete=models.SET_NULL, null=True,
        related_name='path_location'
    )
    order = models.IntegerField()
    distance = models.IntegerField()


class Vehicle(models.Model):
    """Vehicle model.

    Attributes:
    name (CharField): The name of a vehicle.
    """

    name = models.CharField(max_length=10)
    path_id = models.IntegerField()
    location = models.ForeignKey(
        Location, on_delete=models.SET_NULL, null=True,
        related_name='vehicle_location'
    )


class BusStop(models.Model):
    """Bus Stop model.

    Attributes:
    name (CharField): The name of a but stop.
    location (Location): The location of a bus stop.
    """

    name = models.CharField(max_length=128)
    location = models.ForeignKey(
        Location, on_delete=models.CASCADE, related_name='location')
    buses = models.ManyToManyField(Vehicle)
