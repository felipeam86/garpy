#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import pytest
import tempfile
import zipfile
from io import BytesIO
from pathlib import Path
from unittest.mock import Mock

from common import client, get_mocked_request, get_mocked_response
from garpy import Activity, Activities
from garpy.settings import config

RESPONSE_EXAMPLES_PATH = Path(__file__).parent / "response_examples"


@pytest.fixture
def activity():
    activities = json.loads(
        (RESPONSE_EXAMPLES_PATH / "list_activities.json").read_text()
    )
    return Activity.from_garmin_activity_list_entry(activities[0])


class TestActivity:
    """activities.Activity"""

    def test_from_garmin_connect(self, client):
        with client:
            expected_summary = (
                RESPONSE_EXAMPLES_PATH / "summary_9766544337.json"
            ).read_text()
            client.session.get = get_mocked_request(
                status_code=200, func_name="client.session.get()", text=expected_summary
            )
            activity = Activity.from_garmin_connect(9766544337, client)
            assert isinstance(activity, Activity)
            assert activity.id == 9766544337
            assert activity.type == "cycling"
            assert activity.name == "Morning ride"

            client.session.get.assert_called_once()
            client.session.get.assert_called_with(
                config["activities"]["summary"]["endpoint"].format(id=9766544337), params=None
            )

    def test_from_garmin_summary(self):
        summary = json.loads(
            (RESPONSE_EXAMPLES_PATH / "summary_9766544337.json").read_text()
        )

        activity = Activity.from_garmin_summary(summary)
        assert isinstance(activity, Activity)
        assert activity.id == 9766544337
        assert activity.type == "cycling"
        assert activity.name == "Morning ride"

    def test_from_garmin_activity_list_entry(self, activity):
        activities = json.loads(
            (RESPONSE_EXAMPLES_PATH / "list_activities.json").read_text()
        )

        activity = Activity.from_garmin_activity_list_entry(activities[0])
        assert isinstance(activity, Activity)
        assert activity.id == 2532452238
        assert activity.type == "walking"
        assert activity.name == "Random walking"

    def test_filepath_awareness(self, activity):
        expected_base_filename = "2018-11-24T09:30:00+00:00_2532452238"
        backup_dir = Path('/fake/path')
        assert activity.base_filename == expected_base_filename
        assert activity.get_export_filepath(backup_dir, 'gpx') == backup_dir / (expected_base_filename + '.gpx')

        with pytest.raises(ValueError) as excinfo:
            activity.get_export_filepath(backup_dir, 'unknown_format')
        assert (
            f"Format 'unknown_format' unknown."
            in str(excinfo.value)
        )

    def test_download_gpx(self, activity, client):
        with client:
            client.session.get = Mock(
                return_value=get_mocked_response(
                    200, text="Trust me, this is a GPX file"
                ),
                func_name="client.session.get()",
            )
            with tempfile.TemporaryDirectory() as backup_dir:
                fmt = "gpx"
                activity.download(client, fmt, backup_dir)
                expected_downloaded_file_path = activity.get_export_filepath(
                    backup_dir, fmt
                )
                assert expected_downloaded_file_path.exists()
                assert not (Path(backup_dir) / ".not_found").exists()
                assert (
                    expected_downloaded_file_path.read_text()
                    == "Trust me, this is a GPX file"
                )

    def test_download_original(self, activity, client):
        with client:
            response_of_original = (
                RESPONSE_EXAMPLES_PATH / "example_original_with_fit.zip"
            ).read_bytes()
            response_of_original_content = zipfile.ZipFile(
                BytesIO(response_of_original), mode="r"
            )
            fit_inside_original_zip = response_of_original_content.open(
                response_of_original_content.namelist()[0]
            ).read()
            client.session.get = Mock(
                return_value=get_mocked_response(200, content=response_of_original),
                func_name="client.session.get()",
            )
            with tempfile.TemporaryDirectory() as backup_dir:
                fmt = "original"
                activity.download(client, fmt, backup_dir)
                expected_downloaded_file_path = activity.get_export_filepath(
                    backup_dir, fmt
                )
                assert expected_downloaded_file_path.exists()
                assert not (Path(backup_dir) / ".not_found").exists()
                assert (
                    expected_downloaded_file_path.read_bytes()
                    == fit_inside_original_zip
                )

    def test_download_inexistent_gpx(self, activity, client):
        with client:
            client.session.get = Mock(
                return_value=get_mocked_response(404), func_name="client.session.get()"
            )
            with tempfile.TemporaryDirectory() as backup_dir:
                fmt = "gpx"
                activity.download(client, fmt, backup_dir)
                expected_downloaded_file_path = activity.get_export_filepath(
                    backup_dir, fmt
                )
                assert not expected_downloaded_file_path.exists()
                assert (Path(backup_dir) / ".not_found").exists()
                assert (
                    expected_downloaded_file_path.name
                    in (Path(backup_dir) / ".not_found").read_text()
                )

class TestActivities:
    """activities.Activities"""

    def test_list(self):

        client = Mock()
        client.list_activities = Mock(
            return_value=json.loads(
                (RESPONSE_EXAMPLES_PATH / "list_activities.json").read_text()
            )
        )
        activities = Activities.list(client)

        assert isinstance(activities, Activities)
        assert activities[0].id == 2532452238
        assert activities[0].type == "walking"
        assert activities[0].name == "Random walking"
        assert len(activities) == 10
