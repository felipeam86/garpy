#! /usr/bin/env python

"""
A module for authenticating against and communicating with selected parts of the Garmin Connect REST API.

# The client is originally inspired by:
https://github.com/petergardfjall/garminexport

# Other useful reference used by the original garminexport project:
#   https://github.com/cpfair/tapiriik/blob/master/tapiriik/services/GarminConnect/garminconnect.py
"""

import json
from typing import Any, Dict, Tuple

import attr
import pendulum

from .client import GarminClient
from .settings import config, get_logger

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
    def from_garmin_summary(cls, json_summary: str):
        """Constructor based on garmin connect summary.

        Parameters
        ----------
        json_summary
            JSON string representation of summary information fetched from garmin connect
        """

        summary: Dict[str, Any] = json.loads(json_summary)
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
    """

    response = client.get(
        url=ENDPOINTS["JSON_ACTIVITY_SUMMARY"].format(id=activity_id),
        err_message=f"Failed to fetch json activity summary for activity id: {activity_id}.",
    )

    return response.text


def _get_json_details(activity_id: int, client: GarminClient) -> str:
    """Fetch JSON activity details from Garmin Connect.
    """

    response = client.get(
        url=ENDPOINTS["JSON_ACTIVITY_DETAILS"].format(id=activity_id),
        err_message=f"Failed to fetch json activity details for activity id: {activity_id}.",
    )

    return response.text


DOWNLOADERS = {"summary": _get_json_summary, "details": _get_json_details}


@attr.s
class ActivityDownloader:
    """A client class used to download activities from Garmin Connect

    Parameters
    ----------
    activity
        Instance of Activity
    client
        An authenticated GarminClient instance.
    downloaders:
        Dictionary mapping formats to downloader function

    Examples
    --------
    .. code-block:: python

        >>> with GarminClient("my.sample@sample.com", "secretpassword") as client:
        >>>     activity = ActivityDownloader.from_garmin(3983141717, client)
    """

    client: GarminClient = attr.ib()
    activity: Activity = attr.ib(default=None)
    downloaders: Dict[str, Any] = attr.ib(default=DOWNLOADERS)

    @classmethod
    def from_garmin(
        cls,
        activity_id: int,
        client: GarminClient,
        formats: Tuple = tuple(DOWNLOADERS.keys()),
    ):
        if not set(formats).issubset(set(DOWNLOADERS.keys())):
            raise Exception(
                "There is no existent downloader for the following formats: "
                f"{set(formats) - set(DOWNLOADERS.keys())}"
            )

        activity_downloader = cls(
            client=client, downloaders={fmt: DOWNLOADERS[fmt] for fmt in formats}
        )
        json_summary = activity_downloader.get(activity_id, "summary")
        activity_downloader.activity = Activity.from_garmin_summary(json_summary)
        return activity_downloader

    def get(self, activity_id, fmt):
        downloader = self.downloaders.get(fmt)
        if not downloader:
            raise ValueError(
                f"A downloader for the format {fmt} has not been registered"
            )

        return downloader(activity_id, self.client)
