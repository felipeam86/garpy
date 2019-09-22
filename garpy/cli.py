from pathlib import Path
import click

from garpy import GarminClient, ActivitiesDownloader
from garpy.settings import config


@click.group()
@click.version_option()
def main():
    pass


@main.command()
@click.argument("backup-dir", default=config.get("backup-dir"))
@click.option("--formats", "-f", multiple=True)
@click.option(
    "--username",
    "-u",
    prompt=True,
    default=config.get("username"),
    metavar="[Garmin connect username/email]",
)
@click.option(
    "--password",
    "-p",
    prompt=True,
    default=config.get("password"),
    metavar="[Garmin connect password]",
)
def download(backup_dir, formats, username, password):
    """Download activities from Garmin Connect"""
    if not formats:
        formats = tuple(config.get("activities").keys())

    backup_dir = Path(backup_dir).absolute()
    if backup_dir.is_file():
        raise Exception("The provided backup directory exists and is a file")

    with GarminClient(username=username, password=password) as client:
        downloader = ActivitiesDownloader(client=client, backup_dir=backup_dir)
        downloader.download(formats=formats)
