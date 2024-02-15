from __future__ import absolute_import
import json
import requests
from UnleashClient.constants import REQUEST_TIMEOUT, APPLICATION_HEADERS, METRICS_URL
from UnleashClient.utils import LOGGER


# pylint: disable=broad-except
def send_metrics(url,
                 request_body,
                 custom_headers,
                 custom_options):
    """
    Attempts to send metrics to Unleash server

    Notes:
    * If unsuccessful (i.e. not HTTP status code 200), message will be logged

    :param url:
    :param app_name:
    :param instance_id:
    :param metrics_interval:
    :param custom_headers:
    :param custom_options:
    :return: true if registration successful, false if registration unsuccessful or exception.
    """
    try:
        LOGGER.info(u"Sending messages to with unleash @ %s", url)
        LOGGER.info(u"unleash metrics information: %s", request_body)

        headers = custom_headers.copy()
        headers.update(APPLICATION_HEADERS)
        resp = requests.post(url + METRICS_URL,
                             data=json.dumps(request_body),
                             headers=headers,
                             timeout=REQUEST_TIMEOUT, **custom_options)

        if resp.status_code != 202:
            LOGGER.warning(u"unleash metrics submission failed.")
            return False

        LOGGER.info(u"unleash metrics successfully sent!")

        return True
    except Exception:
        LOGGER.exception(u"unleash metrics failed to send.")

    return False
