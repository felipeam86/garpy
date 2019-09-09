#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
from pathlib import Path

from garpy import Activity
from garpy.settings import config
from common import get_client_with_mocked_authenticate, get_mocked_request

RESPONSE_EXAMPLES_PATH = Path(__file__).parent / "response_examples"


class TestActivity:
    """activities.Activity"""

    def test_from_garmin_connect(self):
        clg = get_client_with_mocked_authenticate()
        expected_summary = (
            RESPONSE_EXAMPLES_PATH / "summary_9766544337.json"
        ).read_text()
        with clg:
            clg.session.get = get_mocked_request(
                status_code=200, func_name="clg.session.get()", text=expected_summary
            )
            activity = Activity.from_garmin_connect(9766544337, clg)
            assert isinstance(activity, Activity)
            assert activity.id == 9766544337
            assert activity.type == "cycling"
            assert activity.name == "Morning ride"
            assert activity.summary == json.loads(expected_summary)

            clg.session.get.assert_called_once()
            clg.session.get.assert_called_with(
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
        assert activity.summary == summary

    def test_from_garmin_activity_list_entry(self):
        activities = json.loads(
            (RESPONSE_EXAMPLES_PATH / "list_activities.json").read_text()
        )

        activity = Activity.from_garmin_activity_list_entry(activities[0])
        assert isinstance(activity, Activity)
        assert activity.id == 2532452238
        assert activity.type == "walking"
        assert activity.name == "Random walking"
        assert activity.summary == activities[0]
