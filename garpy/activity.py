#! /usr/bin/env python

"""
A module for authenticating against and communicating with selected parts of the Garmin Connect REST API.

# The client is originally inspired by:
https://github.com/petergardfjall/garminexport

# Other useful reference used by the original garminexport project:
#   https://github.com/cpfair/tapiriik/blob/master/tapiriik/services/GarminConnect/garminconnect.py
"""

import json
from typing import Dict, Any

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
    summary
        Dictionary with json summary downloaded from Garmin

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
    summary: Dict[str, Any] = attr.ib(default={})

    @classmethod
    def from_garmin_summary(cls, summary: str):
        """Constructor based on garmin connect summary.

        Parameters
        ----------
        summary
            JSON string representation of summary information fetched from garmin connect
        """

        summary = json.loads(summary)
        return cls(
            id=summary["activityId"],
            name=summary["activityName"],
            type=summary["activityTypeDTO"]["typeKey"],
            start=pendulum.parse(
                summary["summaryDTO"]["startTimeLocal"],
                tz=summary["timeZoneUnitDTO"]["unitKey"],
            ),
            summary=summary,
        )


def _get_json_summary(activity_id: int, client: GarminClient) -> str:
    """Fetch JSON activity summary from Garmin Connect.

    Parameters
    ----------
    activity_id
        Activity ID on Garmin Connect
    client
        An authenticated GarminClient instance.
    """

    response = client.get(
        url=ENDPOINTS["JSON_ACTIVITY_SUMMARY"].format(id=activity_id),
        err_message=f"Failed to fetch json activity summary for id: {activity_id}.",
    )

    return response.text


def _get_json_details(activity_id: int, client: GarminClient) -> str:
    """Fetch JSON activity details from Garmin Connect.

    Parameters
    ----------
    activity_id
        Activity ID on Garmin Connect
    client
        An authenticated GarminClient instance.
    """

    response = client.get(
        url=ENDPOINTS["JSON_ACTIVITY_DETAILS"].format(id=activity_id),
        err_message=f"Failed to fetch json activity details for id: {activity_id}.",
    )

    return response.text


@attr.s
class ActivityDownloader:
    """A client class used to download activities from Garmin Connect

    Parameters
    ----------
    id
        Activity ID on Garmin Connect
    client
        An authenticated GarminClient instance.

    Examples
    --------
    .. code-block:: python

        >>> with GarminClient("my.sample@sample.com", "secretpassword") as client:
        >>>     activity = ActivityDownloader(3983141717, client)
    """

    client: GarminClient = attr.ib()
    downloaders: Dict[str, Any] = attr.ib(
        default={"summary": _get_json_summary, "details": _get_json_details}
    )

    def get(self, activity_id, fmt):
        downloader = self.downloaders.get(fmt)
        if not downloader:
            raise ValueError(
                f"A downloader for the format {fmt} has not been registered"
            )

        return downloader(activity_id, self.client)

