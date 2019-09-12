#! /usr/bin/env python

import json
from typing import Any, Dict

import attr
import pendulum

from .client import GarminClient


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

    @classmethod
    def from_garmin_summary(cls, summary: Dict[str, Any]):
        """Constructor based on garmin connect summary.

        Parameters
        ----------
        summary
            JSON string representation of summary information fetched from garmin connect
        """

        return cls(
            id=summary["activityId"],
            name=summary["activityName"],
            type=summary["activityTypeDTO"]["typeKey"],
            start=pendulum.parse(
                summary["summaryDTO"]["startTimeLocal"],
                tz=summary["timeZoneUnitDTO"]["unitKey"],
            ),
        )

    @classmethod
    def from_garmin_activity_list_entry(cls, entry: Dict[str, Any]):
        """Constructor based on an entry from the list of activities from garmin connect.

        Parameters
        ----------
        entry
            JSON string representation of an entry of an activity list fetched from garmin connect
        """

        return cls(
            id=entry["activityId"],
            name=entry["activityName"],
            type=entry["activityType"]["typeKey"],
            # Unfortunately, Garmin connect does not provide timezone information on entries from list of activities
            start=pendulum.parse(entry["startTimeGMT"]),
        )

    @classmethod
    def from_garmin_connect(cls, activity_id: int, client: GarminClient):
        response = client.get_activity(activity_id, "summary")
        activity_summary = json.loads(response.text)
        activity = Activity.from_garmin_summary(activity_summary)

        return activity


class Activities(list):
    @classmethod
    def list(cls, client: GarminClient):
        return cls(
            Activity.from_garmin_activity_list_entry(activity)
            for activity in client.list_activities()
        )
