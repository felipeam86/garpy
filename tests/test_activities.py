#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import zipfile
from pathlib import Path
from unittest.mock import Mock

import pytest
from common import client, client_activities, activity, get_mocked_request, get_mocked_response, get_activity

from garpy import Activity, Activities

RESPONSE_EXAMPLES_PATH = Path(__file__).parent / "response_examples"


class TestActivity:
    """activities.Activity"""

    def test_from_garmin_connect(self, client_activities):
        with client_activities:
            activity = Activity.from_garmin_connect(9766544337, client_activities)
            assert isinstance(activity, Activity)
            assert activity.id == 9766544337
            assert activity.type == "cycling"
            assert activity.name == "Morning ride"

            client_activities.get_activity.assert_called_once()
            client_activities.get_activity.assert_called_with(9766544337, "summary")

    def test_from_garmin_summary(self):
        summary = json.loads(
            (RESPONSE_EXAMPLES_PATH / "summary_9766544337.json").read_text()
        )

        activity = Activity.from_garmin_summary(summary)
        assert isinstance(activity, Activity)
        assert activity.id == 9766544337
        assert activity.type == "cycling"
        assert activity.name == "Morning ride"

    def test_from_garmin_activity_list_entry(self):
        activities = json.loads(
            (RESPONSE_EXAMPLES_PATH / "list_activities.json").read_text()
        )

        activity = Activity.from_garmin_activity_list_entry(activities[0])
        assert isinstance(activity, Activity)
        assert activity.id == 2532452238
        assert activity.type == "walking"
        assert activity.name == "Random walking"

    def test_filepath_awareness(self, activity, tmp_path):
        expected_base_filename = "2018-11-24T09:30:00+00:00_2532452238"
        assert activity.base_filename == expected_base_filename
        assert activity.get_export_filepath(tmp_path, "gpx") == tmp_path / (
            expected_base_filename + ".gpx"
        )

        with pytest.raises(ValueError) as excinfo:
            activity.get_export_filepath(tmp_path, "unknown_format")
        assert f"Format 'unknown_format' unknown." in str(excinfo.value)

    def test_download_gpx(self, activity, client_activities, tmp_path):
        with client_activities:
            fmt = "gpx"
            activity.download(client_activities, fmt, tmp_path)
            client_activities.get_activity.assert_called_with(activity.id, fmt)
            client_activities.get_activity.assert_called_once()
            expected_downloaded_file_path = activity.get_export_filepath(tmp_path, fmt)
            assert expected_downloaded_file_path.exists()
            assert not (Path(tmp_path) / ".not_found").exists()
            assert (
                expected_downloaded_file_path.read_text()
                == f"Trust me, this is a {fmt!r} file for activity {activity.id!r}"
            )

    def test_download_original(self, activity, client_activities, tmp_path):
        with client_activities:
            fmt = "original"
            activity.download(client_activities, fmt, tmp_path)
            client_activities.get_activity.assert_called_with(activity.id, fmt)
            client_activities.get_activity.assert_called_once()
            expected_downloaded_file_path = activity.get_export_filepath(tmp_path, fmt)
            assert expected_downloaded_file_path.exists()
            assert not (Path(tmp_path) / ".not_found").exists()
            zipped_file = zipfile.ZipFile(RESPONSE_EXAMPLES_PATH / "example_original_with_fit.zip", mode="r")
            fit_inside_original_zip = zipped_file.open(zipped_file.namelist()[0]).read()
            assert expected_downloaded_file_path.read_bytes() == fit_inside_original_zip

    def test_download_inexistent_gpx(self, activity, client, tmp_path):
        with client:
            client.session.get = Mock(
                return_value=get_mocked_response(404), func_name="client.session.get()"
            )
            fmt = "gpx"
            activity.download(client, fmt, tmp_path)
            expected_downloaded_file_path = activity.get_export_filepath(tmp_path, fmt)
            assert not expected_downloaded_file_path.exists()
            assert (Path(tmp_path) / ".not_found").exists()
            assert (
                expected_downloaded_file_path.name
                in (Path(tmp_path) / ".not_found").read_text()
            )


class TestActivities:
    """activities.Activities"""

    def test_list(self, client_activities):

        activities = Activities.list(client_activities)

        assert isinstance(activities, Activities)
        assert activities[0].id == 2532452238
        assert activities[0].type == "walking"
        assert activities[0].name == "Random walking"
        assert len(activities) == 10
