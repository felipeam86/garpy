import json
import pytest
from pathlib import Path
from unittest.mock import Mock

from garpy import GarminClient, Activity

RESPONSE_EXAMPLES_PATH = Path(__file__).parent / "response_examples"


@pytest.fixture
def activity():
    activities = json.loads(
        (RESPONSE_EXAMPLES_PATH / "list_activities.json").read_text()
    )
    return Activity.from_garmin_activity_list_entry(activities[0])


@pytest.fixture
def client():
    clg = GarminClient(username="dummy", password="dummy")
    clg._authenticate = Mock(return_value=None, name="clg._authenticate()")
    return clg


@pytest.fixture
def client_activities(client):
    activities = json.loads(
        (RESPONSE_EXAMPLES_PATH / "list_activities.json").read_text()
    )
    assert len(activities) == 10
    client.list_activities = Mock(return_value=activities)
    client.get_activity = Mock(side_effect=get_activity)
    return client


def get_mocked_response(status_code, text=None, content=None):
    failed_response = Mock()
    failed_response.status_code = status_code
    failed_response.text = text or ""
    failed_response.content = content or b""
    return failed_response


def get_mocked_request(status_code=200, func_name=None, text=None):
    return Mock(return_value=get_mocked_response(status_code, text), name=func_name)


def get_activity(activity_id, fmt):
    if fmt == "original":
        return get_mocked_response(
            status_code=200,
            content=(
                RESPONSE_EXAMPLES_PATH / "example_original_with_fit.zip"
            ).read_bytes(),
        )
    else:
        if (fmt == 'summary') and (activity_id == 9766544337):
            text = (RESPONSE_EXAMPLES_PATH / "summary_9766544337.json").read_text()
        else:
            text = f"Trust me, this is a {fmt!r} file for activity {activity_id!r}"

        return get_mocked_response(
            status_code=200,
            text=text,
        )
