from __future__ import absolute_import
import requests
from UnleashClient.constants import REQUEST_TIMEOUT, FEATURES_URL
from UnleashClient.utils import LOGGER


# pylint: disable=broad-except
def get_feature_toggles(url,
                        app_name,
                        instance_id,
                        custom_headers,
                        custom_options):
    """
    Retrieves feature flags from unleash central server.

    Notes:
    * If unsuccessful (i.e. not HTTP status code 200), exception will be caught and logged.
      This is to allow "safe" error handling if unleash server goes down.

    :param url:
    :param app_name:
    :param instance_id:
    :param custom_headers:
    :param custom_options:
    :return: Feature flags if successful, empty dict if not.
    """
    try:
        LOGGER.info(u"Getting feature flag.")

        headers = {
            u"UNLEASH-APPNAME": app_name,
            u"UNLEASH-INSTANCEID": instance_id
        }
        _headers = custom_headers.copy()
        _headers.update(headers)
        resp = requests.get(url + FEATURES_URL,
                            headers=_headers,
                            timeout=REQUEST_TIMEOUT, **custom_options)

        if resp.status_code != 200:
            LOGGER.warning(u"unleash feature fetch failed!")
            raise Exception(u"unleash feature fetch failed!")

        return resp.json()
    except Exception:
        LOGGER.exception(u"Unleash feature fetch failed!")

    return {}
