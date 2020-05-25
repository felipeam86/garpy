#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pathlib import Path
from unittest.mock import Mock

import pendulum
import pytest
from conftest import get_mocked_response

from garpy import Wellness

RESPONSE_EXAMPLES_PATH = Path(__file__).parent / "response_examples"


class TestActivity:
    """activities.Activity"""

    def test_instantiation(self, tmp_path):
        date = pendulum.DateTime(2019, 9, 27)
        wellness = Wellness(date)
        assert wellness.base_filename == "2019-09-27.zip"
        assert wellness.get_export_filepath(tmp_path) == tmp_path / "2019-09-27.zip"

    def test_wont_travel_to_future(self):
        date = pendulum.DateTime.today().add(days=1)
        with pytest.raises(ValueError) as excinfo:
            _ = Wellness(date)

        assert (
            f"garpy cannot download data from the future... "
            f"try a date before today {date.format('YYYY-MM-DD')}" in str(excinfo.value)
        )

    def test_download(self, client_wellness, tmp_path):
        date = pendulum.DateTime(2019, 9, 27)
        wellness = Wellness(date)
        with client_wellness:
            wellness.download(client_wellness, tmp_path)
            client_wellness.get_wellness.assert_called_once()
            client_wellness.get_wellness.assert_called_with(date)
            expected_downloaded_file_path = wellness.get_export_filepath(tmp_path)
            assert expected_downloaded_file_path.exists()
            assert not (Path(tmp_path) / ".not_found").exists()
            zipped_file = RESPONSE_EXAMPLES_PATH / "example_original_with_fit.zip"
            assert (
                expected_downloaded_file_path.read_bytes() == zipped_file.read_bytes()
            )

    def test_download_inexistent_day(self, client, tmp_path):
        date = pendulum.DateTime(2019, 9, 27)
        wellness = Wellness(date)
        with client:
            client.session.get = Mock(
                return_value=get_mocked_response(404), func_name="client.session.get()"
            )
            wellness.download(client, tmp_path)
            expected_downloaded_file_path = wellness.get_export_filepath(tmp_path)
            assert not expected_downloaded_file_path.exists()
            assert (Path(tmp_path) / ".not_found").exists()
            assert (
                expected_downloaded_file_path.name
                in (Path(tmp_path) / ".not_found").read_text()
            )
