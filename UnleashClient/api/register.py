from __future__ import absolute_import
import json
from datetime import datetime
from dateutil.tz import tzutc
import requests
from UnleashClient.constants import SDK_NAME, SDK_VERSION, REQUEST_TIMEOUT, APPLICATION_HEADERS, REGISTER_URL
from UnleashClient.utils import LOGGER


# pylint: disable=broad-except
def register_client(url,
                    app_name,
                    instance_id,
                    metrics_interval,
                    custom_headers,
                    custom_options,
                    supported_strategies):
    """
    Attempts to register client with unleash server.

    Notes:
    * If unsuccessful (i.e. not HTTP status code 202), exception will be caught and logged.
      This is to allow "safe" error handling if unleash server goes down.

    :param url:
    :param app_name:
    :param instance_id:
    :param metrics_interval:
    :param custom_headers:
    :param custom_options:
    :param supported_strategies:
    :return: true if registration successful, false if registration unsuccessful or exception.
    """
    registation_request = {
        u"appName": app_name,
        u"instanceId": instance_id,
        u"sdkVersion": u"{}:{}".format(SDK_NAME, SDK_VERSION),
        u"strategies": supported_strategies.keys(),
        u"started": datetime.now(tzutc()).isoformat(),
        u"interval": metrics_interval
    }

    try:
        LOGGER.info(u"Registering unleash client with unleash @ %s", url)
        LOGGER.info(u"Registration request information: %s", registation_request)

        headers = custom_headers.copy()
        headers.update(APPLICATION_HEADERS)
        resp = requests.post(url + REGISTER_URL,
                             data=json.dumps(registation_request),
                             headers=headers,
                             timeout=REQUEST_TIMEOUT, **custom_options)

        if resp.status_code != 202:
            LOGGER.warning(u"unleash client registration failed.")
            return False

        LOGGER.info(u"unleash client successfully registered!")

        return True
    except Exception:
        LOGGER.exception(u"unleash client registration failed.")

    return False
