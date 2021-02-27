#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from garpy import cli


class TestCLI:
    """cli.main"""

    def test_download_username_password_only(self):
        with patch.object(cli.GarminClient, "_authenticate", return_value=None):
            with patch.object(cli.ActivitiesDownloader, "__call__", return_value=None):
                runner = CliRunner()
                with runner.isolated_filesystem():
                    result = runner.invoke(
                        cli.main, ["download", "-u", "dummy", "-p", "password"]
                    )
                    assert result.exit_code == 0

    def test_download_several_formats(self):
        with patch.object(cli.GarminClient, "_authenticate", return_value=None):
            with patch.object(cli.ActivitiesDownloader, "__call__", return_value=None):
                runner = CliRunner()
                with runner.isolated_filesystem():
                    result = runner.invoke(
                        cli.main,
                        [
                            "download",
                            "-u",
                            "dummy",
                            "-p",
                            "password",
                            "-f",
                            "gpx",
                            "-f",
                            "fit",
                        ],
                    )
                    assert result.exit_code == 0

    def test_download_fails_with_existing_file_as_bakcup_dir(self, tmp_path):
        with patch.object(cli.GarminClient, "_authenticate", return_value=None):
            with patch.object(cli.ActivitiesDownloader, "__call__", return_value=None):
                runner = CliRunner()
                with runner.isolated_filesystem():
                    backup_dir = Path(tmp_path) / "text_file"
                    backup_dir.touch()
                    result = runner.invoke(
                        cli.main,
                        ["download", "-u", "dummy", "-p", "password", str(backup_dir)],
                    )
                    assert result.exit_code == 1
                    assert (
                        str(result.exception)
                        == "The provided backup directory exists and is a file"
                    )
