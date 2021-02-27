#! /usr/bin/env python

import logging
from pathlib import Path
from typing import Dict

import attr

from . import Activities, Activity, GarminClient
from .settings import config

logger = logging.getLogger(__name__)

DEFAULT_FORMATS = tuple(config["activities"].keys())


@attr.s
class ActivitiesDownloader:
    """Class for doing incremental backups of your Garmin activitiess

    Parameters
    ----------
    client
        Authenticated GarminClient
    backup_dir
        Where to download the file
    """

    client: GarminClient = attr.ib()
    backup_dir: Path = attr.ib(default=config["backup-dir"])

    @backup_dir.validator
    def enforce_path(self, attribute, value):
        """Make sure that self.backup_dir is cast into Path and that it exits"""
        if isinstance(value, str):
            self.backup_dir = Path(value)
        self.backup_dir = self.backup_dir.absolute()
        self.backup_dir.mkdir(exist_ok=True)

    @property
    def existing_files(self):
        """Set of existing files on the backup directory"""
        return set(filepath for filepath in self.backup_dir.glob("*"))

    @property
    def not_found(self):
        """Set of files not found on a previous backup try"""
        if (self.backup_dir / ".not_found").exists():
            return set(
                self.backup_dir / path.strip()
                for path in (self.backup_dir / ".not_found").read_text().split("\n")
                if path
            )
        else:
            return set()

    def _discover_formats_to_download(
        self, activities: Activities, formats: tuple = DEFAULT_FORMATS
    ) -> Dict[Activity, tuple]:
        """Fetch list of activities and find which of them need backup and in what formats"""

        files_not_to_download = self.existing_files | self.not_found
        to_download = {}
        for activity in activities:
            needed_formats = tuple(
                fmt
                for fmt in formats
                if activity.get_export_filepath(self.backup_dir, fmt)
                not in files_not_to_download
            )
            if needed_formats:
                to_download[activity] = needed_formats

        return to_download

    def download_all(self, activities: Activities, formats: tuple = DEFAULT_FORMATS):
        """Do an incremental backup of the specified formats.

        Parameters
        ----------
        activities
            List of activities fetched from Garmin Connect
        formats
            Formats you wish to download
        """
        to_download = self._discover_formats_to_download(activities, formats)
        if not to_download:
            logger.info("Backup folder up to date. No activities will be downloaded")
            return

        n_activities = len(to_download)
        logger.info(f"{n_activities} activities to be downloaded")

        to_download = progressbar(to_download.items())
        for i, (activity, formats) in enumerate(to_download):
            to_download.desc = (
                f"Downloading {activity.type!r} activity {activity.id!r} "
                f"from {activity.start.format('YYYY-MM-DD')}. Formats: {formats!r}"
            )
            to_download.display()
            formats = progressbar(formats, leave=(i + 1 == n_activities))
            for fmt in formats:
                formats.desc = f"Downloading format {fmt!r}"
                formats.display()
                activity.download(self.client, fmt, self.backup_dir)

    def download_one(self, activity: Activity, formats: tuple = DEFAULT_FORMATS):
        """Download specified formats for a given activity

        Parameters
        ----------
        activity
            Activity you wish to download
        formats
            Formats you wish to download
        """
        logger.info(
            f"Downloading {activity.type!r} activity {activity.id!r} "
            f"from {activity.start.format('YYYY-MM-DD')}."
        )
        formats = progressbar(formats, leave=True)
        for fmt in formats:
            formats.desc = f"Downloading format {fmt!r}"
            formats.display()
            activity.download(self.client, fmt, self.backup_dir)

    def __call__(self, formats: tuple = DEFAULT_FORMATS, activity_id: int = None):
        logger.info(
            f"Downloading the following formats: {formats!r} "
            f"to this folder: {self.backup_dir}"
        )
        if activity_id is None:
            logger.info("Querying list of activities")
            activities = Activities.list(self.client)
            logger.info(
                f"{len(activities)} activities in total found on Garmin Connect"
            )
            self.download_all(activities=activities, formats=formats)
        else:
            logger.info(f"Fetching summary information for activity: {activity_id!r}")
            activity = Activity.from_garmin_connect(activity_id, self.client)
            self.download_one(activity=activity, formats=formats)


def _isnotebook():  # pragma: no cover
    """Check if garpy is being run inside a Jupyter notebook"""
    try:
        shell = get_ipython().__class__.__name__
        return shell == "ZMQInteractiveShell"
    except NameError:
        return False  # Probably standard Python interpreter or IPython


def progressbar(*args, **kwargs):  # pragma: no cover
    """Make a progress bar depending on the environment garpy is running"""
    if _isnotebook():
        from tqdm import tqdm_notebook as tqdm
    else:
        from tqdm import tqdm

    return tqdm(*args, **kwargs)
