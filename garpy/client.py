#! /usr/bin/env python

"""
A module for authenticating against and communicating with selected parts of the Garmin Connect REST API.

# The client is originally inspired by:
https://github.com/petergardfjall/garminexport

# Other useful reference used by the original garminexport project:
https://github.com/cpfair/tapiriik/blob/master/tapiriik/services/GarminConnect/garminconnect.py
"""

import json
import logging
import re
import sys
from typing import Dict, List, Tuple

import attr
import cloudscraper
import pendulum
import requests

from .settings import Password, config

logger = logging.getLogger(__name__)
ENDPOINTS = config["endpoints"]


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
        raise ConnectionError(
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
    password: str = attr.ib(
        default=config.get("password").get(), repr=False, converter=Password
    )
    session: requests.Session = attr.ib(default=None, repr=False)
    user_agent: str = attr.ib(default=config["user-agent"])

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.disconnect()

    def connect(self):
        if (not bool(self.username)) or (not bool(self.password)):
            raise ConnectionError(
                "Missing credentials. Your forgot to provide username or password. "
                f"username: '{self.username}'. password: '{self.password}'"
            )
        self.session = self.session or cloudscraper.create_scraper(
            browser={
                "browser": "firefox",
                "platform": "windows",
                "mobile": False,
            }
        )

        self._authenticate()

    def disconnect(self):
        if self.session:
            self.session.close()
            self.session = None

    def _authenticate(self):
        logger.info(f"Authenticating {self!r}")
        auth_response = self.session.post(
            ENDPOINTS["SSO_LOGIN_URL"],
            headers={
                "origin": "https://sso.garmin.com",
                "User-Agent": self.user_agent,
            },
            params={"service": "https://connect.garmin.com/modern"},
            data={
                "username": self.username,
                "password": self.password.get(),
                "embed": "false",
            },
        )
        logger.debug("got auth response: %s", auth_response.text)
        if auth_response.status_code != 200:
            raise ConnectionError(
                "authentication failure: did you enter valid credentials?"
            )
        auth_ticket_url = extract_auth_ticket_url(auth_response.text)

        logger.info("Claiming auth ticket")
        response = self.session.get(auth_ticket_url)
        if response.status_code != 200:
            raise ConnectionError(
                f"auth failure: failed to claim auth ticket: {auth_ticket_url}: {response.status_code}\n{response.text}"
            )

        # appears like we need to touch base with the old API to initiate
        # some form of legacy session. otherwise certain downloads will fail.
        self.session.get("https://connect.garmin.com/legacy/session")

    @property
    def connected(self) -> bool:
        return self.session is not None

    def get(
        self, url: str, err_message: str, tolerate: Tuple = (), params: dict = None
    ) -> requests.Response:
        """Send a get request on an authenticated session and tolerate some response codes

        Parameters
        ----------
        url
            Endpoint you want to query
        err_message
            In case of error, this message will be logged and raised with an exception
        tolerate
            Wich HTML response codes to tolerate.
        params
            URL parameters to append to the URL.
        Returns
        -------
        Response of the GET query
        """

        if not self.connected:
            raise ConnectionError(
                "Attempt to use GarminClient without being connected. Call connect() before first use."
            )

        response = self.session.get(url, params=params)
        if response.status_code in tolerate:
            return response
        elif response.status_code != 200:
            err_message += f"\nResponse code: {response.status_code}\n{response.text}"
            logger.error(err_message)
            raise ConnectionError(err_message)
        else:
            return response

    def get_activity(self, activity_id, fmt) -> requests.Response:
        """Get an activity from its ID on the requested format

        Parameters
        ----------
        activity_id
            Activity ID on Garmin Connect
        fmt
            Format you wish to download.

        Returns
        -------
        requests.Response
            Response content of the request to Garmin Connect
        """
        format_parameters = config["activities"].get(fmt)
        if not format_parameters:
            raise ValueError(
                f"Parameters for downloading the format '{fmt}' have not been provided."
            )

        response = self.get(
            url=format_parameters["endpoint"].format(id=activity_id),
            err_message=f"Failed to fetch '{fmt}' for activity id {activity_id}.",
            tolerate=tuple(format_parameters.get("tolerate", tuple())),
        )
        return response

    def list_activities(self) -> List[Dict]:
        """List all historical activities on Garmin Connect."""
        batch_size = 100
        activities = []
        for start_index in range(0, sys.maxsize, batch_size):
            response = self.get(
                url=config["endpoints"]["ACTIVITY_LIST"],
                params={"start": start_index, "limit": batch_size},
                err_message=f"Failed to fetch activities {start_index} to {start_index + batch_size - 1}.",
            )
            next_batch = json.loads(response.text)
            if not next_batch:
                break
            activities.extend(next_batch)

        return activities

    def get_wellness(self, date: pendulum.DateTime) -> requests.Response:
        """Get wellness data for a given date

        Parameters
        ----------
        date
            Date for which you want to fetch wellness data

        Returns
        -------
        requests.Response
            Response content of the request to Garmin Connect
        """

        response = self.get(
            url=config["wellness"]["endpoint"].format(date=date.format("YYYY-MM-DD")),
            err_message=f"Failed to fetch wellness data for date {date!r}.",
            tolerate=tuple(config["wellness"]["tolerate"]),
        )
        return response
