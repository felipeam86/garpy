#! /usr/bin/env python

import json
import os
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Any, Dict

import attr
import pendulum

from .client import GarminClient
from .settings import config


@attr.s(frozen=True)
class Activity:
    """Garmin activity

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

    @property
    def base_filename(self):
        filename = f"{self.start.in_tz('UTC').isoformat()}_{self.id}"
        if os.name == "nt":  # Windows complains about : in filenames.
            filename = filename.replace(":", ".")
        return filename

    def get_export_filepath(self, backup_dir: Path, fmt: str) -> Path:
        format_parameters = config["activities"].get(fmt)
        if not format_parameters:
            raise ValueError(f"Format '{fmt}' unknown.")
        return Path(backup_dir) / (self.base_filename + format_parameters["suffix"])

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
        """Constructor that fetches activity summary from Garmin Connect

        Parameters
        ----------
        activity_id
            Activity ID on Garmin Connect
        client
            Authenticated GarminClient
        """
        response = client.get_activity(activity_id, "summary")
        activity_summary = json.loads(response.text)
        activity = Activity.from_garmin_summary(activity_summary)

        return activity

    def download(self, client: GarminClient, fmt: str, backup_dir: Path) -> None:
        """Download activity on the given format to the given backup directory

        Parameters
        ----------
        client
            Authenticated GarminClient
        fmt
            Format you wish to download
        backup_dir
            Where to download the file
        """
        response = client.get_activity(self.id, fmt)
        filepath = self.get_export_filepath(backup_dir, fmt)
        backup_dir = Path(backup_dir)
        backup_dir.mkdir(exist_ok=True)
        if response.status_code == 200:
            if fmt == "original":
                zip_content = zipfile.ZipFile(BytesIO(response.content), mode="r")
                original_file_name = zip_content.namelist()[0]
                fit_bytes = zip_content.open(original_file_name).read()
                # Change file extension to the one on the zipped file
                filepath = filepath.with_suffix(Path(original_file_name).suffix)
                filepath.write_bytes(fit_bytes)

                # If original format is not FIT, register it as not found
                if filepath.suffix != ".fit":
                    with open(
                        str(Path(backup_dir) / ".not_found"), mode="a"
                    ) as not_found:
                        not_found.write(
                            str(self.get_export_filepath(backup_dir, fmt).name) + "\n"
                        )
            else:
                filepath.write_text(response.text)
        else:
            with open(str(Path(backup_dir) / ".not_found"), mode="a") as not_found:
                not_found.write(str(filepath.name) + "\n")


class Activities(list):
    @classmethod
    def list(cls, client: GarminClient):
        return cls(
            Activity.from_garmin_activity_list_entry(activity)
            for activity in client.list_activities()
        )
