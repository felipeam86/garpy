import pytest
from unittest.mock import Mock

from garpy import GarminClient


@pytest.fixture
def client():
    clg = GarminClient(username="dummy", password="dummy")
    clg._authenticate = Mock(return_value=None, name="clg._authenticate()")
    return clg


def get_mocked_response(status_code, text=None, content=None):
    failed_response = Mock()
    failed_response.status_code = status_code
    failed_response.text = text or ""
    failed_response.content = content or b""
    return failed_response


def get_mocked_request(status_code=200, func_name=None, text=None):
    return Mock(return_value=get_mocked_response(status_code, text), name=func_name)
