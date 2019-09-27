#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
from pathlib import Path

import pendulum
import pytest
import requests
from unittest.mock import Mock

from garpy.client import extract_auth_ticket_url
from garpy import GarminClient
from garpy.settings import config, Password
from common import (
    client,
    get_mocked_request,
    get_mocked_response
)

RESPONSE_EXAMPLES_PATH = Path(__file__).parent / "response_examples"


class TestExtractAuthTicketUrl:
    def test_with_good_response(self):
        auth_response_extract = 'var response_url                    =\n"https:\/\/connect.garmin.com\/modern?ticket=DG-2742319-qf4sfe2315ddfQFQ3dYc-cas";'
        url = extract_auth_ticket_url(auth_response_extract)
        assert (
            url
            == "https://connect.garmin.com/modern?ticket=DG-2742319-qf4sfe2315ddfQFQ3dYc-cas"
        )

    def test_raises_connection_error(self):

        with pytest.raises(ConnectionError) as excinfo:
            auth_response_extract = (
                "Random response that does not contain the authentication ticket"
            )
            url = extract_auth_ticket_url(auth_response_extract)
        assert (
            "auth failure: unable to extract auth ticket URL. did you provide a correct username/password?"
            in str(excinfo.value)
        )


class TestGarminClient:
    """client.GarminClient"""

    def test_connect_and_disconnet(self, client):
        """Test expected behavior of .connect() and disconnect()"""

        assert not client.connected, "Client should not be connected"
        client.connect()
        client._authenticate.assert_called_once()
        assert (
            client.connected
        ), "Client should be connected after authentication"
        client.disconnect()
        assert not client.connected, "Client should be disconnected after disconnecting"

    def test_connect_fails_with_empty_username_password(self):
        """Test that .connect() raises ConnectionError with missing/empty credentials"""

        client = GarminClient(username="", password="falsepassword")
        with pytest.raises(ConnectionError) as excinfo:
            client.connect()

        err_msg = f"Missing credentials. Your forgot to provide username or password. " \
                  f"username: ''. password: '*************'"
        assert err_msg in str(excinfo.value)

        client = GarminClient(username="falseuser", password="")
        with pytest.raises(ConnectionError) as excinfo:
            client.connect()

        err_msg = f"Missing credentials. Your forgot to provide username or password. " \
                  f"username: 'falseuser'. password: ''"
        assert err_msg in str(excinfo.value)

        client = GarminClient(username="", password="")
        with pytest.raises(ConnectionError) as excinfo:
            client.connect()

        err_msg = f"Missing credentials. Your forgot to provide username or password. " \
                  f"username: ''. password: ''"
        assert err_msg in str(excinfo.value)

    def test_authentication_fail_raises_error(self):
        """Test that .connect() raises ConnectionError with dummy credentials"""
        client = GarminClient(username="falseuser", password="falsepassword")
        client.session = requests.Session()
        client.session.post = get_mocked_request(
            status_code=400,
            func_name="client.session.post()",
        )
        with pytest.raises(ConnectionError):
            client.connect()

    def test_client_context_manager_session_management(self, client):
        """Test that context managers creates and destroys the session"""
        assert not client.connected, "Client should not be connected"
        with client:
            client._authenticate.assert_called_once()
            assert (
                client.connected
            ), "The client should be connected within the with statement"

        assert not client.connected, "Client should have disconnected after with statement"

    def test_authenticate_with_string_password(self):
        """Test normal behavior of _authenticate"""
        client = GarminClient(username="falseuser", password="falsepassword")
        client.session = requests.Session()
        client.session.post = get_mocked_request(
            status_code=200,
            func_name="client.session.post()",
            text='var response_url                    =\n"https:\/\/connect.garmin.com\/modern?ticket=DG-2742319-qf4sfe2315ddfQFQ3dYc-cas";',
        )
        client.session.get = get_mocked_request(
            status_code=200, func_name="client.session.get()"
        )
        client.connect()

    def test_authenticate_with_Password_password(self):
        """Test normal behavior of _authenticate"""
        client = GarminClient(username="falseuser", password=Password("falsepassword"))
        client.session = requests.Session()
        client.session.post = get_mocked_request(
            status_code=200,
            func_name="client.session.post()",
            text='var response_url                    =\n"https:\/\/connect.garmin.com\/modern?ticket=DG-2742319-qf4sfe2315ddfQFQ3dYc-cas";',
        )
        client.session.get = get_mocked_request(
            status_code=200, func_name="client.session.get()"
        )
        client.connect()

        client.session.post.assert_called_with(
            config["endpoints"]["SSO_LOGIN_URL"],
            headers={"origin": "https://sso.garmin.com"},
            params={"service": "https://connect.garmin.com/modern"},
            data={
                "username": 'falseuser',
                "password": "falsepassword",
                "embed": "false",
            },
        )

        assert (
            str(client.password) == "*************"
        ), "The password has not been succesfully hidden on string representation"
        assert (
            client.password.get() == "falsepassword"
        ), "The original password was not recovered with the .get() method"

    def test_authenticate_auth_ticket_fails_get_auth_ticket(self):
        """Test that _authenticate fails if it does not get auth ticket"""
        client = GarminClient(username="falseuser", password="falsepassword")
        client.session = requests.Session()
        client.session.post = get_mocked_request(
            status_code=200,
            func_name="client.session.post()",
            text="Random response that does not contain the authentication ticket",
        )
        client.session.get = get_mocked_request(
            status_code=200, func_name="client.session.get()"
        )
        with pytest.raises(ConnectionError) as excinfo:
            client.connect()
        err_msg = "auth failure: unable to extract auth ticket URL. did you provide a correct username/password?"
        assert err_msg in str(excinfo.value)

    def test_authenticate_auth_ticket_fails_on_post(self):
        """Test that _authenticate fails if it does not get auth ticket"""
        client = GarminClient(username="falseuser", password="falsepassword")
        client.session = requests.Session()
        client.session.post = get_mocked_request(
            status_code=404, func_name="client.session.post()"
        )
        client.session.get = get_mocked_request(
            status_code=200, func_name="client.session.get()"
        )
        with pytest.raises(ConnectionError) as excinfo:
            client.connect()
        err_msg = "authentication failure: did you enter valid credentials?"
        assert err_msg in str(excinfo.value)

    def test_authenticate_auth_ticket_fails_on_get(self):
        """Test that _authenticate fails if it does not get auth ticket"""
        client = GarminClient(username="falseuser", password="falsepassword")
        client.session = requests.Session()
        client.session.post = get_mocked_request(
            status_code=200,
            func_name="client.session.post()",
            text='var response_url                    =\n"https:\/\/connect.garmin.com\/modern?ticket=DG-2742319-qf4sfe2315ddfQFQ3dYc-cas";',
        )
        client.session.get = get_mocked_request(
            status_code=404, func_name="client.session.get()"
        )
        with pytest.raises(ConnectionError) as excinfo:
            client.connect()
        err_msg = "auth failure: failed to claim auth ticket:"
        assert err_msg in str(excinfo.value)

    def test_get(self, client):
        with client:
            client.session.get = get_mocked_request(
                status_code=200, func_name="client.session.get()", text="I'm working"
            )
            response = client.get(url="dummy_url", err_message="")
            assert response.text == "I'm working"

    def test_get_raises_exception_on_non_authed_session(self, client):
        """Test that .get() command only works with authenticated sessions"""
        with pytest.raises(ConnectionError) as excinfo:
            client.get(url="dummy_url", err_message="")
        assert (
            "Attempt to use GarminClient without being connected. Call connect() before first use."
            in str(excinfo.value)
        )

    def test_get_raises_error_with_status_code_different_200(self, client):
        with client:
            client.session.get = get_mocked_request(
                status_code=404, func_name="client.session.get()"
            )
            with pytest.raises(ConnectionError) as excinfo:
                client.get(url="dummy_url", err_message="")
            assert f"Response code: 404" in str(excinfo.value)
            client.session.get.assert_called_once()

    def test_get_tolerates_error_codes(self, client):
        with client:
            client.session.get = get_mocked_request(
                status_code=404, func_name="client.session.get()"
            )
            client.get(url="dummy_url", err_message="", tolerate=(404,))
            client.session.get.assert_called_once()

    def test_get_activity(self, client):
        with client:
            for fmt, parameters in config["activities"].items():
                # Test normal behavior with 200 response code
                client.session.get = get_mocked_request(
                    status_code=200, func_name="client.session.get()"
                )
                client.get_activity(9766544337, fmt)
                client.session.get.assert_called_once()
                client.session.get.assert_called_with(
                    parameters["endpoint"].format(id=9766544337), params=None
                )

                # Test raised exception with 400 response code
                client.session.get = get_mocked_request(
                    status_code=400, func_name="client.session.get()"
                )
                with pytest.raises(ConnectionError) as excinfo:
                    client.get_activity(9766544337, fmt)
                assert f"Response code: 400" in str(excinfo.value)

                client.session.get.assert_called_once()
                client.session.get.assert_called_with(
                    parameters["endpoint"].format(id=9766544337), params=None
                )

                # Test error codes get tolerated
                if parameters.get("tolerate") is not None:
                    for code in parameters.get("tolerate"):
                        client.session.get = get_mocked_request(
                            status_code=code, func_name="client.session.get()"
                        )
                        client.get_activity(9766544337, fmt)
                        client.session.get.assert_called_once()
                        client.session.get.assert_called_with(
                            parameters["endpoint"].format(id=9766544337), params=None
                        )

    def test_get_activity_raises_error_unknown_format(self, client):
        with client:
            with pytest.raises(ValueError) as excinfo:
                client.get_activity(9766544337, "random_format")

            assert (
                f"Parameters for downloading the format 'random_format' have not been provided."
                in str(excinfo.value)
            )

    def test_list_activities(self, client):
        first_batch = (RESPONSE_EXAMPLES_PATH  / "list_activities.json").read_text()
        with client:
            client.session.get = Mock(
                side_effect=[
                    get_mocked_response(200, first_batch),
                    get_mocked_response(200, '[]')
                ],
                func_name="client.session.get()"
            )
            activities = client.list_activities()

            assert client.session.get.call_count == 2

        assert activities == json.loads(first_batch)

    def test_get_wellness(self, client):
        endpoint = config["wellness"]["endpoint"]
        date = pendulum.DateTime(2019, 9, 27)
        with client:
            # Test normal behavior with 200 response code
            client.session.get = get_mocked_request(
                status_code=200, func_name="client.session.get()"
            )
            client.get_wellness(date)
            client.session.get.assert_called_once()
            client.session.get.assert_called_with(
                endpoint.format(date='2019-09-27'), params=None
            )

            # Test raised exception with 400 response code
            client.session.get = get_mocked_request(
                status_code=400, func_name="client.session.get()"
            )
            with pytest.raises(ConnectionError) as excinfo:
                client.get_wellness(date)
            assert f"Response code: 400" in str(excinfo.value)

            client.session.get.assert_called_once()
            client.session.get.assert_called_with(
                endpoint.format(date='2019-09-27'), params=None
            )

            # Test error codes get tolerated
            tolerate = tuple(config["wellness"].get("tolerate"))
            if tolerate is not None:
                for code in tuple(config["wellness"]["tolerate"]):
                    client.session.get = get_mocked_request(
                        status_code=code, func_name="client.session.get()"
                    )
                    client.get_wellness(date)
                    client.session.get.assert_called_once()
                    client.session.get.assert_called_with(
                        endpoint.format(date='2019-09-27'), params=None
                    )
