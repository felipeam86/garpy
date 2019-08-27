#! /usr/bin/env python

"""
A module for authenticating against and communicating with selected parts of the Garmin Connect REST API.

# The client is originally inspired by:
https://github.com/petergardfjall/garminexport

# Other useful reference used by the original garminexport project:
#   https://github.com/cpfair/tapiriik/blob/master/tapiriik/services/GarminConnect/garminconnect.py
"""

import json

import attr
import pendulum

from .settings import config, get_logger
from .client import GarminClient

logger = get_logger(__name__)
ENDPOINTS = config["endpoints"]


@attr.s
class Activity:
    """Garmin activity identifier

    Parameters
    ----------
    id
        Activity ID on Garmin Connect
    name
        Name of the activity
    type
        Type of activity, e.g, Cycling, Swimming, etc
    start
        Start date and time

    Examples
    --------
    .. code-block:: python

        >>> with GarminClient("my.sample@sample.com", "secretpassword") as client:
        >>>     activity = Activity.from_garmin_connect(3983141717, client)

    """

    id: int = attr.ib()
    name: str = attr.ib()
    type: str = attr.ib()
    start: pendulum.DateTime = attr.ib()

    @classmethod
    def from_garmin_connect(cls, activity_id, client):
        """Constructor that fetches activity summary from Garmin Connect.

        Parameters
        ----------
        activity_id
            Activity ID on Garmin Connect
        client
            An authenticated GarminClient instance.
        """

        if not client.session:
            raise Exception(
                "Attempt to use GarminClient without being connected. Call connect() before first use."
            )

        response = client.session.get(
            ENDPOINTS["ACTIVITY_SUMMARY"].format(id=activity_id)
        )
        if response.status_code != 200:
            err_message = f"Failed to fetch json summary for activity {activity_id}: {response.status_code}\n{response.text}"
            logger.error(err_message)
            raise Exception(err_message)

        summary = json.loads(response.text)
        start = pendulum.parse(
            summary["summaryDTO"]["startTimeLocal"],
            tz=summary["timeZoneUnitDTO"]["unitKey"],
        )
        return cls(
            id=activity_id,
            name=summary["activityName"],
            type=summary["activityTypeDTO"]["typeKey"],
            start=start,
        )
