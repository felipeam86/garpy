from pathlib import Path
import click

from garpy import GarminClient, ActivitiesDownloader
from garpy.settings import config

FORMATS = set(config.get("activities").keys()) | {'fit'}

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
    metavar="[Garmin connect username/email]",
)
@click.option(
    "--password",
    "-p",
    prompt=True,
    default=config.get("password"),
    metavar="[Garmin connect password]",
    hide_input=True,
)
def download(backup_dir, formats, username, password):
    """Download activities from Garmin Connect"""
    if 'fit' in formats:
        formats = set(formats)
        formats.remove('fit')
        formats.add('original')
        formats = tuple(formats)

    backup_dir = Path(backup_dir).absolute()
    if backup_dir.is_file():
        raise Exception("The provided backup directory exists and is a file")

    with GarminClient(username=username, password=password) as client:
        downloader = ActivitiesDownloader(client=client, backup_dir=backup_dir)
        downloader.download(formats=formats)
