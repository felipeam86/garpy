#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pathlib import Path
from unittest.mock import Mock

from common import client, activity, client_activities, get_mocked_response, get_activity

from garpy import ActivitiesDownloader, Activity, Activities
from garpy.download import DEFAULT_FORMATS

RESPONSE_EXAMPLES_PATH = Path(__file__).parent / "response_examples"


class TestActivitiesDownloader:
    """download.ActivitiesDownloader"""

    def test_backup_dir_with_path(self, client, tmp_path):
        downloader = ActivitiesDownloader(client, tmp_path)
        assert downloader.backup_dir.exists()
        assert downloader.backup_dir == tmp_path

    def test_backup_dir_with_str(self, client, tmp_path):
        downloader = ActivitiesDownloader(client, str(tmp_path))
        assert isinstance(downloader.backup_dir, Path)
        assert downloader.backup_dir.exists()
        assert downloader.backup_dir == tmp_path

    def test_backup_dir_inexistent(self, client, tmp_path):
        tmp_path.rmdir()
        assert not tmp_path.exists()
        downloader = ActivitiesDownloader(client, str(tmp_path))
        assert downloader.backup_dir.exists()
        assert downloader.backup_dir == tmp_path

    def test_existing_files_is_empty(self, client, tmp_path):
        downloader = ActivitiesDownloader(client, tmp_path)
        assert downloader.existing_files == set()

    def test_existing_files_has_file_after_download(self, activity, client, tmp_path):
        with client:
            client.session.get = Mock(
                return_value=get_mocked_response(
                    200, text="Trust me, this is a GPX file"
                ),
                func_name="client.session.get()",
            )
            fmt = "gpx"
            activity.download(client, fmt, tmp_path)

        downloader = ActivitiesDownloader(client, tmp_path)
        assert downloader.existing_files == {
            activity.get_export_filepath(tmp_path, fmt)
        }

    def test_not_found_inexistent(self, client, tmp_path):
        downloader = ActivitiesDownloader(client, str(tmp_path))
        assert not (downloader.backup_dir / ".not_found").exists()
        assert downloader.not_found == set()

    def test_not_found_empty(self, client, tmp_path):
        downloader = ActivitiesDownloader(client, str(tmp_path))
        (downloader.backup_dir / ".not_found").touch()
        assert (downloader.backup_dir / ".not_found").exists()
        assert downloader.not_found == set()

    def test_not_found_has_file_after_failed_download(self, activity, client, tmp_path):
        with client:
            client.session.get = Mock(
                return_value=get_mocked_response(404), func_name="client.session.get()"
            )
            fmt = "gpx"
            activity.download(client, fmt, tmp_path)

        downloader = ActivitiesDownloader(client, tmp_path)
        assert downloader.not_found == {activity.get_export_filepath(tmp_path, fmt)}

    def test_discover_formats_to_download_with_backup_from_scratch(self, client_activities, tmp_path):
        activities = client_activities.list_activities()
        assert len(activities) == 10
        with client_activities:
            downloader = ActivitiesDownloader(client_activities, tmp_path)
            to_download = downloader._discover_formats_to_download(Activities.list(client_activities))

        assert len(to_download) == 10
        for activity, formats in to_download.items():
            assert set(formats) == set(DEFAULT_FORMATS)

    def test_discover_formats_to_download_with_incremental_backup(self, client_activities, tmp_path):
        activities = client_activities.list_activities()
        assert len(activities) == 10
        with client_activities:
            activity = Activity.from_garmin_activity_list_entry(activities[0])
            for fmt in DEFAULT_FORMATS:
                activity.download(client_activities, fmt, tmp_path)
            downloader = ActivitiesDownloader(client_activities, tmp_path)
            to_download = downloader._discover_formats_to_download(Activities.list(client_activities))

        assert len(to_download) == 9
        for activity, formats in to_download.items():
            assert set(formats) == set(DEFAULT_FORMATS)

    def test_discover_formats_to_download_with_not_found(self, client_activities, tmp_path):
        activities = client_activities.list_activities()
        assert len(activities) == 10
        with client_activities:
            # Download one activity manually first
            activity = Activity.from_garmin_activity_list_entry(activities[0])
            (tmp_path / ".not_found").write_text(
                str(activity.get_export_filepath(tmp_path, "gpx"))
            )

            # Discover what should be downloaded
            downloader = ActivitiesDownloader(client_activities, tmp_path)
            to_download = downloader._discover_formats_to_download(Activities.list(client_activities))

        assert len(to_download) == 10
        for activity, formats in to_download.items():
            if len(formats) < len(DEFAULT_FORMATS):
                assert "gpx" not in formats
                assert set(formats) <= set(DEFAULT_FORMATS)
            else:
                assert set(formats) == set(DEFAULT_FORMATS)

    def test_discover_formats_to_download_with_backup_up_to_date(self, client_activities, tmp_path):
        activities = client_activities.list_activities()
        assert len(activities) == 10
        with client_activities:
            # Download everything manually first
            for activity_entry in activities:
                activity = Activity.from_garmin_activity_list_entry(activity_entry)
                for fmt in DEFAULT_FORMATS:
                    activity.download(client_activities, fmt, tmp_path)

            # Discover what should be downloaded
            downloader = ActivitiesDownloader(client_activities, tmp_path)
            to_download = downloader._discover_formats_to_download(Activities.list(client_activities))

        assert len(to_download) == 0

    def test_download_with_backup_from_scratch(self, client_activities, tmp_path):
        assert len(list(tmp_path.glob('*'))) == 0
        with client_activities:
            # Discover what should be downloaded
            downloader = ActivitiesDownloader(client_activities, tmp_path)
            downloader.download_all(Activities.list(client_activities))
            assert len(list(tmp_path.glob('*'))) == 50

    def test_download_with_backup_up_to_date(self, client_activities, tmp_path):
        activities = client_activities.list_activities()
        assert len(list(tmp_path.glob('*'))) == 0
        with client_activities:
            # Download everything manually first
            for activity_entry in activities:
                activity = Activity.from_garmin_activity_list_entry(activity_entry)
                for fmt in DEFAULT_FORMATS:
                    activity.download(client_activities, fmt, tmp_path)

            assert len(list(tmp_path.glob('*'))) == 50
            downloader = ActivitiesDownloader(client_activities, tmp_path)
            downloader.download_all(Activities.list(client_activities))
            assert len(list(tmp_path.glob('*'))) == 50

    def test_download_with_backup_up_to_date_and_files_not_found(self, client_activities, tmp_path):
        activities = client_activities.list_activities()
        assert len(list(tmp_path.glob('*'))) == 0
        with client_activities:
            # Download everything manually first and fake that GPX was not found for all activities
            for activity_entry in activities:
                activity = Activity.from_garmin_activity_list_entry(activity_entry)
                for fmt in DEFAULT_FORMATS:
                    if fmt == 'gpx':
                        with open(str(Path(tmp_path) / ".not_found"), mode="a") as not_found:
                            not_found.write(str(activity.get_export_filepath(tmp_path, fmt).name) + "\n")
                    else:
                        activity.download(client_activities, fmt, tmp_path)

            assert len(list(tmp_path.glob('*'))) == 41
            downloader = ActivitiesDownloader(client_activities, tmp_path)
            downloader.download_all(Activities.list(client_activities))
            assert len(list(tmp_path.glob('*'))) == 41

    def test_download_with_files_not_found(self, client_activities, tmp_path):
        activities = client_activities.list_activities()
        assert len(list(tmp_path.glob('*'))) == 0
        with client_activities:
            # Fake that GPX was not found for all activities
            for activity_entry in activities:
                activity = Activity.from_garmin_activity_list_entry(activity_entry)
                for fmt in DEFAULT_FORMATS:
                    if fmt == 'gpx':
                        with open(str(Path(tmp_path) / ".not_found"), mode="a") as not_found:
                            not_found.write(str(activity.get_export_filepath(tmp_path, fmt).name) + "\n")

            assert len(list(tmp_path.glob('*'))) == 1, "There should be a '.not_found' file in the backup directory"
            downloader = ActivitiesDownloader(client_activities, tmp_path)
            downloader.download_all(Activities.list(client_activities))
            assert len(list(tmp_path.glob('*'))) == 41

    def test_download_with_files_not_found_and_some_backed_up(self, client_activities, tmp_path):
        activities = client_activities.list_activities()
        assert len(list(tmp_path.glob('*'))) == 0
        with client_activities:
            # Fake that GPX was not found for all activities
            for activity_entry in activities[:5]:
                activity = Activity.from_garmin_activity_list_entry(activity_entry)
                for fmt in DEFAULT_FORMATS:
                    if fmt == 'gpx':
                        with open(str(Path(tmp_path) / ".not_found"), mode="a") as not_found:
                            not_found.write(str(activity.get_export_filepath(tmp_path, fmt).name) + "\n")
                    else:
                        activity.download(client_activities, fmt, tmp_path)

            assert len(list(tmp_path.glob('*'))) == 21
            downloader = ActivitiesDownloader(client_activities, tmp_path)
            downloader.download_all(Activities.list(client_activities))
            assert len(list(tmp_path.glob('*'))) == 46

    def test_download_one_activity_with_backup_from_scratch(self, client_activities, tmp_path):
        assert len(list(tmp_path.glob('*'))) == 0
        with client_activities:
            activity = Activity.from_garmin_connect(9766544337, client_activities)

            # Discover what should be downloaded
            downloader = ActivitiesDownloader(client_activities, tmp_path)
            downloader.download_one(activity)
            assert len(list(tmp_path.glob('*'))) == 5

    def test_call_for_all_activities(self, client_activities, tmp_path):
        assert len(list(tmp_path.glob('*'))) == 0
        with client_activities:
            # Discover what should be downloaded
            downloader = ActivitiesDownloader(client_activities, tmp_path)
            downloader()
            assert len(list(tmp_path.glob('*'))) == 50

    def test_call_for_one_activity(self, client_activities, tmp_path):
        assert len(list(tmp_path.glob('*'))) == 0
        with client_activities:
            # Discover what should be downloaded
            downloader = ActivitiesDownloader(client_activities, tmp_path)
            downloader(activity_id=9766544337)
            assert len(list(tmp_path.glob('*'))) == 5
