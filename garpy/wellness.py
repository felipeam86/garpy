#! /usr/bin/env python

from dataclasses import dataclass
from pathlib import Path

import pendulum
from garpyclient import GarminClient


@dataclass
class Wellness:
    """Garmin wellness data


    Parameters
    ----------
    date
        Date for which you want to fetch wellness data

    """

    date: pendulum.DateTime

    def __post_init__(self):
        if self.date.in_tz("local") > pendulum.DateTime.today().in_tz("local"):
            raise ValueError(
                f"garpy cannot download data from the future... "
                f"try a date before today {self.date.format('YYYY-MM-DD')}"
            )

    @property
    def base_filename(self) -> str:
        return self.date.format("YYYY-MM-DD") + ".zip"

    def get_export_filepath(self, backup_dir: Path) -> Path:
        return Path(backup_dir) / self.base_filename

    def download(self, client: GarminClient, backup_dir: Path) -> None:
        """Download activity on the given format to the given backup directory

        Parameters
        ----------
        client
            Authenticated GarminClient
        backup_dir
            Where to download the file
        """
        response = client.get_wellness(self.date)
        backup_dir = Path(backup_dir)
        backup_dir.mkdir(exist_ok=True)
        filepath = self.get_export_filepath(backup_dir)
        if response.status_code == 200:
            filepath.write_bytes(response.content)
        else:
            with open(str(Path(backup_dir) / ".not_found"), mode="a") as not_found:
                not_found.write(str(filepath.name) + "\n")
