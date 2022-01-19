from pathlib import Path

import click

from garpy import ActivitiesDownloader, GarminClient
from garpy.settings import config

FORMATS = set(config.get("activities").keys()) | {"fit"}


@click.group()
@click.version_option()
def main():
    pass


@main.command()
@click.argument("backup-dir", default=config.get("backup-dir"))
@click.option(
    "--formats",
    "-f",
    multiple=True,
    help="Which formats to download. The flag can be used several times, e.g. '-f original -f gpx'",
    type=click.Choice(FORMATS),
    show_choices=True,
    default=FORMATS,
)
@click.option(
    "--username",
    "-u",
    prompt=True,
    default=config.get("username"),
    metavar="{username}",
    help="Username of your Garmin account",
)
@click.option(
    "--password",
    "-p",
    prompt=True,
    default=config.get("password").get(),
    metavar="{password}",
    help="Password of your Garmin account",
    hide_input=True,
)
@click.option(
    "--activity",
    "-a",
    "activity_id",
    default=None,
    metavar="{ID}",
    help="Activity ID. If indicated, download only that activity, even if it has already been downloaded."
    " Otherwise, do incremental update of backup",
    hide_input=True,
)
@click.option(
    "--user-agent",
    "user_agent",
    default=config["user-agent"],
    metavar="{user_agent}",
    help="User agent to be used by requests",
    hide_input=True,
)
def download(backup_dir, formats, username, password, activity_id, user_agent):
    """Download activities from Garmin Connect

    Entry point for downloading activities from Garmin Connect. By default, it downloads all
    newly created activities since the last time you did a backup.

    If you specify an activity ID with the "-a/--activity" flag, only that activity will be downloaded,
    even if it has already been downloaded before.

    If no format is specified, the app will download all possible formats. Otherwise you can specify the
    formats you wish to download with the "-f/--formats" flag. The flag can be used several  times if you
    wish to specify several formats, e.g., 'garpy download [OPTIONS] -f original -f gpx [BACKUP_DIR]' will
    download .fit and .gpx files
    """
    if "fit" in formats:
        formats = set(formats)
        formats.remove("fit")
        formats.add("original")
        formats = tuple(formats)

    backup_dir = Path(backup_dir).absolute()
    if backup_dir.is_file():
        raise Exception("The provided backup directory exists and is a file")

    with GarminClient(
        username=username, password=password, user_agent=user_agent
    ) as client:
        downloader = ActivitiesDownloader(client=client, backup_dir=backup_dir)
        downloader(formats=formats, activity_id=activity_id)
