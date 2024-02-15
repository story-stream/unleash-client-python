from __future__ import absolute_import
from chainmap import ChainMap
from datetime import datetime
from dateutil.tz import tzutc
import fcache
from UnleashClient.api import send_metrics
from UnleashClient.constants import METRIC_LAST_SENT_TIME


def aggregate_and_send_metrics(url,
                               app_name,
                               instance_id,
                               custom_headers,
                               custom_options,
                               features,
                               ondisk_cache
                               ):
    feature_stats_list = []

    for feature_name in features.keys():
        feature_stats = {
            features[feature_name].name: {
                u"yes": features[feature_name].yes_count,
                u"no": features[feature_name].no_count
            }
        }

        features[feature_name].reset_stats()
        feature_stats_list.append(feature_stats)

    metrics_request = {
        u"appName": app_name,
        u"instanceId": instance_id,
        u"bucket": {
            u"start": ondisk_cache[METRIC_LAST_SENT_TIME].isoformat(),
            u"stop": datetime.now(tzutc()).isoformat(),
            u"toggles": dict(ChainMap(*feature_stats_list))
        }
    }

    send_metrics(url, metrics_request, custom_headers, custom_options)
    ondisk_cache[METRIC_LAST_SENT_TIME] = datetime.now(tzutc())
    ondisk_cache.sync()
