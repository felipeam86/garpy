#! /usr/bin/env python

"""
A module for authenticating against and communicating with selected parts of the Garmin Connect REST API.

# The client is originally inspired by:
https://github.com/petergardfjall/garminexport

# Other useful reference used by the original garminexport project:
https://github.com/cpfair/tapiriik/blob/master/tapiriik/services/GarminConnect/garminconnect.py
"""

import re
from functools import wraps
from typing import Callable

import attr
import requests

from .settings import config, get_logger

logger = get_logger(__name__)
ENDPOINTS = config["endpoints"]


def require_session(client_function: Callable):
    """Decorator that guarantees that there is an active authenticated session

    Parameters
    ----------
    client_function : Callable
        Method of the class :class:`GarminClient`

    Returns
    -------
    Decorated method that verifies an active authenticated connection before running
    """

    @wraps(client_function)
    def check_session(*args, **kwargs):
        client_object = args[0]
        if not client_object.session:
            raise Exception(
                "Attempt to use GarminClient without being connected. Call connect() before first use.'"
            )
        return client_function(*args, **kwargs)

    return check_session


def extract_auth_ticket_url(auth_response: str):
    """Extract authentication ticket URL from response of authentication form submission.

    The auth ticket URL is typically of form:

    https://connect.garmin.com/modern?ticket=ST-0123456-aBCDefgh1iJkLmN5opQ9R-cas

    Parameters
    ----------
    auth_response :
        HTML response from an auth form submission.

    Returns
    -------
    str
        Authentication ticket url
    """

    match = re.search(r'response_url\s*=\s*"(https:[^"]+)"', auth_response)
    if not match:
        raise RuntimeError(
            "auth failure: unable to extract auth ticket URL. did you provide a correct username/password?"
        )
    auth_ticket_url = match.group(1).replace("\\", "")
    logger.debug("auth ticket url: '%s'", auth_ticket_url)
    return auth_ticket_url


@attr.s
class GarminClient(object):
    """A client class used to authenticate with Garmin Connect

    Since this class implements the context manager protocol, this object
    can preferably be used together with the with-statement. This will
    automatically take care of logging in to Garmin Connect before any
    further interactions and logging out after the block completes or
    a failure occurs.

    Parameters
    ----------
    username
        Garmin connect username or email address
    password
        Garmin connect password
    session
        A Requests session

    Examples
    --------
    .. code-block:: python

        >>> with GarminClient("my.sample@sample.com", "secretpassword") as client:
        >>>     response = client.session.get(
        >>>         "https://connect.garmin.com/modern/{endpoint}",
        >>>         params={...},
        >>>     )

    """

    username: str = attr.ib(default=config.get("username"))
    password: str = attr.ib(default=config.get("password"), repr=False)
    session: requests.Session = attr.ib(default=requests.Session(), repr=False)

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.disconnect()

    def connect(self):
        self._authenticate()

    def disconnect(self):
        if self.session:
            self.session.close()
            self.session = None

    def _authenticate(self):
        logger.info("authenticating user ...")
        auth_response = self.session.post(
            ENDPOINTS["SSO_LOGIN_URL"],
            headers={"origin": "https://sso.garmin.com"},
            params={"service": "https://connect.garmin.com/modern"},
            data={
                "username": self.username,
                "password": self.password,
                "embed": "false",
            },
        )
        logger.debug("got auth response: %s", auth_response.text)
        if auth_response.status_code != 200:
            raise ValueError("authentication failure: did you enter valid credentials?")
        auth_ticket_url = extract_auth_ticket_url(auth_response.text)

        logger.info("claiming auth ticket ...")
        response = self.session.get(auth_ticket_url)
        if response.status_code != 200:
            raise RuntimeError(
                f"auth failure: failed to claim auth ticket: {auth_ticket_url}: {response.status_code}\n{response.text}"
            )

        # appears like we need to touch base with the old API to initiate
        # some form of legacy session. otherwise certain downloads will fail.
        self.session.get("https://connect.garmin.com/legacy/session")
