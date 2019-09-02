#!/usr/bin/env python
# -*- coding: utf-8 -*-

from unittest.mock import Mock
import pytest
import requests

from garpy import client


def get_client_with_mocked_authenticate():
    clg = client.GarminClient(username="dummy", password="dummy")
    clg._authenticate = Mock(return_value=None, name="clg._authenticate()")
    return clg


def get_mocked_request(status_code=200, func_name=None, text=None):
    failed_response = Mock()
    failed_response.status_code = status_code
    failed_response.text = text or ""
    return Mock(return_value=failed_response, name=func_name)


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

        assert clg.session is None, "Session should be empty before connecting"
        clg.connect()
        clg._authenticate.assert_called_once()
        assert (
            clg.session is not None
        ), "A session should have been created after connection"
        clg.disconnect()
        assert clg.session is None, "Session should be empty after disconnecting"

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
        assert clg.session is None, "Session should be empty before with statement"
        with clg:
            clg._authenticate.assert_called_once()
            assert (
                clg.session is not None
            ), "A session should have been created within the with statement"

        assert clg.session is None, "Session should be empty after with statement"

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
