#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
import requests

from garpy import client
from garpy.settings import config
from common import get_client_with_mocked_authenticate, get_mocked_request


class TestExtractAuthTicketUrl:
    def test_with_good_response(self):
        auth_response_extract = 'var response_url                    =\n"https:\/\/connect.garmin.com\/modern?ticket=DG-2742319-qf4sfe2315ddfQFQ3dYc-cas";'
        url = client.extract_auth_ticket_url(auth_response_extract)
        assert (
            url
            == "https://connect.garmin.com/modern?ticket=DG-2742319-qf4sfe2315ddfQFQ3dYc-cas"
        )

    def test_raises_connection_error(self):

        with pytest.raises(ConnectionError) as excinfo:
            auth_response_extract = (
                "Random response that does not contain the authentication ticket"
            )
            url = client.extract_auth_ticket_url(auth_response_extract)
        assert (
            "auth failure: unable to extract auth ticket URL. did you provide a correct username/password?"
            in str(excinfo.value)
        )


class TestGarminClient:
    """client.GarminClient"""

    def test_connect_and_disconnet(self):
        """Test expected behavior of .connect() and disconnect()"""
        clg = get_client_with_mocked_authenticate()

        assert not clg.connected, "Client should not be connected"
        clg.connect()
        clg._authenticate.assert_called_once()
        assert (
            clg.connected
        ), "Client should be connected after authentication"
        clg.disconnect()
        assert not clg.connected, "Client should be disconnected after disconnecting"

    def test_connect_fails_with_empty_username_password(self):
        """Test that .connect() raises ConnectionError with missing/empty credentials"""

        clg = client.GarminClient(username="", password="falsepassword")
        with pytest.raises(ConnectionError) as excinfo:
            clg.connect()

        err_msg = f"Missing credentials. Your forgot to provide username or password. " \
                  f"username: ''. password: 'falsepassword'"
        assert err_msg in str(excinfo.value)

        clg = client.GarminClient(username="falseuser", password="")
        with pytest.raises(ConnectionError) as excinfo:
            clg.connect()

        err_msg = f"Missing credentials. Your forgot to provide username or password. " \
                  f"username: 'falseuser'. password: ''"
        assert err_msg in str(excinfo.value)

        clg = client.GarminClient(username="", password="")
        with pytest.raises(ConnectionError) as excinfo:
            clg.connect()

        err_msg = f"Missing credentials. Your forgot to provide username or password. " \
                  f"username: ''. password: ''"
        assert err_msg in str(excinfo.value)

    def test_authentication_fail_raises_error(self):
        """Test that .connect() raises ConnectionError with dummy credentials"""
        clg = client.GarminClient(username="falseuser", password="falsepassword")
        with pytest.raises(ConnectionError):
            clg.connect()

    def test_client_context_manager_session_management(self):
        """Test that context managers creates and destroys the session"""

        clg = get_client_with_mocked_authenticate()
        assert not clg.connected, "Client should not be connected"
        with clg:
            clg._authenticate.assert_called_once()
            assert (
                clg.connected
            ), "The client should be connected within the with statement"

        assert not clg.connected, "Client should have disconnected after with statement"

    def test_authenticate(self):
        """Test normal behavior of _authenticate"""
        clg = client.GarminClient(username="falseuser", password="falsepassword")
        clg.session = requests.Session()
        clg.session.post = get_mocked_request(
            status_code=200,
            func_name="clg.session.post()",
            text='var response_url                    =\n"https:\/\/connect.garmin.com\/modern?ticket=DG-2742319-qf4sfe2315ddfQFQ3dYc-cas";',
        )
        clg.session.get = get_mocked_request(
            status_code=200, func_name="clg.session.get()"
        )
        clg.connect()

    def test_authenticate_auth_ticket_fails_get_auth_ticket(self):
        """Test that _authenticate fails if it does not get auth ticket"""
        clg = client.GarminClient(username="falseuser", password="falsepassword")
        clg.session = requests.Session()
        clg.session.post = get_mocked_request(
            status_code=200,
            func_name="clg.session.post()",
            text="Random response that does not contain the authentication ticket",
        )
        clg.session.get = get_mocked_request(
            status_code=200, func_name="clg.session.get()"
        )
        with pytest.raises(ConnectionError) as excinfo:
            clg.connect()
        err_msg = "auth failure: unable to extract auth ticket URL. did you provide a correct username/password?"
        assert err_msg in str(excinfo.value)

    def test_authenticate_auth_ticket_fails_on_post(self):
        """Test that _authenticate fails if it does not get auth ticket"""
        clg = client.GarminClient(username="falseuser", password="falsepassword")
        clg.session = requests.Session()
        clg.session.post = get_mocked_request(
            status_code=404, func_name="clg.session.post()"
        )
        clg.session.get = get_mocked_request(
            status_code=200, func_name="clg.session.get()"
        )
        with pytest.raises(ConnectionError) as excinfo:
            clg.connect()
        err_msg = "authentication failure: did you enter valid credentials?"
        assert err_msg in str(excinfo.value)

    def test_authenticate_auth_ticket_fails_on_get(self):
        """Test that _authenticate fails if it does not get auth ticket"""
        clg = client.GarminClient(username="falseuser", password="falsepassword")
        clg.session = requests.Session()
        clg.session.post = get_mocked_request(
            status_code=200,
            func_name="clg.session.post()",
            text='var response_url                    =\n"https:\/\/connect.garmin.com\/modern?ticket=DG-2742319-qf4sfe2315ddfQFQ3dYc-cas";',
        )
        clg.session.get = get_mocked_request(
            status_code=404, func_name="clg.session.get()"
        )
        with pytest.raises(ConnectionError) as excinfo:
            clg.connect()
        err_msg = "auth failure: failed to claim auth ticket:"
        assert err_msg in str(excinfo.value)

    def test_get(self):
        clg = get_client_with_mocked_authenticate()
        with clg:
            clg.session.get = get_mocked_request(
                status_code=200, func_name="clg.session.get()", text="I'm working"
            )
            response = clg.get(url="dummy_url", err_message="")
            assert response.text == "I'm working"

    def test_get_raises_exception_on_non_authed_session(self):
        """Test that .get() command only works with authenticated sessions"""
        with pytest.raises(ConnectionError) as excinfo:
            clg = get_client_with_mocked_authenticate()
            clg.get(url="dummy_url", err_message="")
        assert (
            "Attempt to use GarminClient without being connected. Call connect() before first use."
            in str(excinfo.value)
        )

    def test_get_raises_error_with_status_code_different_200(self):
        clg = get_client_with_mocked_authenticate()
        with clg:
            clg.session.get = get_mocked_request(
                status_code=404, func_name="clg.session.get()"
            )
            with pytest.raises(ConnectionError) as excinfo:
                clg.get(url="dummy_url", err_message="")
            assert f"Response code: 404" in str(excinfo.value)
            clg.session.get.assert_called_once()

    def test_get_tolerates_error_codes(self):
        clg = get_client_with_mocked_authenticate()
        with clg:
            clg.session.get = get_mocked_request(
                status_code=404, func_name="clg.session.get()"
            )
            clg.get(url="dummy_url", err_message="", tolerate=(404,))
            clg.session.get.assert_called_once()

    def test_get_activity(self):
        clg = get_client_with_mocked_authenticate()
        with clg:
            for fmt, parameters in config["activities"].items():
                # Test normal behavior with 200 response code
                clg.session.get = get_mocked_request(
                    status_code=200, func_name="clg.session.get()"
                )
                clg.get_activity(9766544337, fmt)
                clg.session.get.assert_called_once()
                clg.session.get.assert_called_with(
                    parameters["endpoint"].format(id=9766544337)
                )

                # Test raised exception with 400 response code
                clg.session.get = get_mocked_request(
                    status_code=400, func_name="clg.session.get()"
                )
                with pytest.raises(ConnectionError) as excinfo:
                    clg.get_activity(9766544337, fmt)
                assert f"Response code: 400" in str(excinfo.value)

                clg.session.get.assert_called_once()
                clg.session.get.assert_called_with(
                    parameters["endpoint"].format(id=9766544337)
                )

                # Test error codes get tolerated
                if parameters.get("tolerate") is not None:
                    for code in parameters.get("tolerate"):
                        clg.session.get = get_mocked_request(
                            status_code=code, func_name="clg.session.get()"
                        )
                        clg.get_activity(9766544337, fmt)
                        clg.session.get.assert_called_once()
                        clg.session.get.assert_called_with(
                            parameters["endpoint"].format(id=9766544337)
                        )

    def test_get_activity_raises_error_unknown_format(self):
        clg = get_client_with_mocked_authenticate()
        with clg:
            with pytest.raises(ValueError) as excinfo:
                clg.get_activity(9766544337, "random_format")

            assert (
                f"Parameters for downloading the format 'random_format' have not been provided."
                in str(excinfo.value)
            )
