from __future__ import absolute_import
from datetime import datetime
from dateutil.tz import tzutc
from typing import Dict
from fcache.cache import FileCache
from apscheduler.job import Job
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from UnleashClient.api import register_client
from UnleashClient.periodic_tasks import fetch_and_load_features, aggregate_and_send_metrics
from UnleashClient.strategies import ApplicationHostname, Default, GradualRolloutRandom, \
    GradualRolloutSessionId, GradualRolloutUserId, UserWithId, RemoteAddress, FlexibleRollout
from UnleashClient.constants import METRIC_LAST_SENT_TIME
from .utils import LOGGER
from .deprecation_warnings import strategy_v2xx_deprecation_check


# pylint: disable=dangerous-default-value
class UnleashClient(object):
    """
    Client implementation.

    """
    def __init__(self,
                 url,
                 app_name,
                 environment = u"default",
                 instance_id = u"unleash-client-python",
                 refresh_interval = 15,
                 metrics_interval = 60,
                 disable_metrics = False,
                 disable_registration = False,
                 custom_headers = {},
                 custom_options = {},
                 custom_strategies = {},
                 cache_directory = None):
        """
        A client for the Unleash feature toggle system.

        :param url: URL of the unleash server, required.
        :param app_name: Name of the application using the unleash client, required.
        :param environment: Name of the environment using the unleash client, optinal & defaults to "default".
        :param instance_id: Unique identifier for unleash client instance, optional & defaults to "unleash-client-python"
        :param refresh_interval: Provisioning refresh interval in ms, optional & defaults to 15 seconds
        :param metrics_interval: Metrics refresh interval in ms, optional & defaults to 60 seconds
        :param disable_metrics: Disables sending metrics to unleash server, optional & defaults to false.
        :param custom_headers: Default headers to send to unleash server, optional & defaults to empty.
        :param custom_options: Default requests parameters, optional & defaults to empty.
        :param custom_strategies: Dictionary of custom strategy names : custom strategy objects
        :param cache_directory: Location of the cache directory. When unset, FCache will determine the location
        """
        # Configuration
        self.unleash_url = url.rstrip(u'\\')
        self.unleash_app_name = app_name
        self.unleash_environment = environment
        self.unleash_instance_id = instance_id
        self.unleash_refresh_interval = refresh_interval
        self.unleash_metrics_interval = metrics_interval
        self.unleash_disable_metrics = disable_metrics
        self.unleash_disable_registration = disable_registration
        self.unleash_custom_headers = custom_headers
        self.unleash_custom_options = custom_options
        self.unleash_static_context = {
            u"appName": self.unleash_app_name,
            u"environment": self.unleash_environment
        }

        # Class objects
        self.cache = FileCache(self.unleash_instance_id, app_cache_dir=cache_directory)
        self.features = {}  # type: Dict
        self.scheduler = BackgroundScheduler()
        self.fl_job = None  # type: Job
        self.metric_job = None  # type: Job
        self.cache[METRIC_LAST_SENT_TIME] = datetime.now(tzutc())
        self.cache.sync()

        # Mappings
        default_strategy_mapping = {
            u"applicationHostname": ApplicationHostname,
            u"default": Default,
            u"gradualRolloutRandom": GradualRolloutRandom,
            u"gradualRolloutSessionId": GradualRolloutSessionId,
            u"gradualRolloutUserId": GradualRolloutUserId,
            u"remoteAddress": RemoteAddress,
            u"userWithId": UserWithId,
            u"flexibleRollout": FlexibleRollout
        }

        if custom_strategies:
            strategy_v2xx_deprecation_check([x for x in custom_strategies.values()])  # pylint: disable=R1721

        self.strategy_mapping = {}
        self.strategy_mapping.update(custom_strategies)
        self.strategy_mapping.update(default_strategy_mapping)

        # Client status
        self.is_initialized = False

    def initialize_client(self):
        """
        Initializes client and starts communication with central unleash server(s).

        This kicks off:
        * Client registration
        * Provisioning poll
        * Stats poll

        :return:
        """
        # Setup
        fl_args = {
            u"url": self.unleash_url,
            u"app_name": self.unleash_app_name,
            u"instance_id": self.unleash_instance_id,
            u"custom_headers": self.unleash_custom_headers,
            u"custom_options": self.unleash_custom_options,
            u"cache": self.cache,
            u"features": self.features,
            u"strategy_mapping": self.strategy_mapping
        }

        metrics_args = {
            u"url": self.unleash_url,
            u"app_name": self.unleash_app_name,
            u"instance_id": self.unleash_instance_id,
            u"custom_headers": self.unleash_custom_headers,
            u"custom_options": self.unleash_custom_options,
            u"features": self.features,
            u"ondisk_cache": self.cache
        }

        # Register app
        if not self.unleash_disable_registration:
            register_client(self.unleash_url, self.unleash_app_name, self.unleash_instance_id,
                            self.unleash_metrics_interval, self.unleash_custom_headers,
                            self.unleash_custom_options, self.strategy_mapping)

        fetch_and_load_features(**fl_args)

        # Start periodic jobs
        self.scheduler.start()
        self.fl_job = self.scheduler.add_job(fetch_and_load_features,
                                             trigger=IntervalTrigger(seconds=int(self.unleash_refresh_interval)),
                                             kwargs=fl_args)

        if not self.unleash_disable_metrics:
            self.metric_job = self.scheduler.add_job(aggregate_and_send_metrics,
                                                     trigger=IntervalTrigger(seconds=int(self.unleash_metrics_interval)),
                                                     kwargs=metrics_args)

        self.is_initialized = True

    def destroy(self):
        """
        Gracefully shuts down the Unleash client by stopping jobs, stopping the scheduler, and deleting the cache.

        You shouldn't need this too much!

        :return:
        """
        self.fl_job.remove()
        if self.metric_job:
            self.metric_job.remove()
        self.scheduler.shutdown()
        self.cache.delete()

    # pylint: disable=broad-except
    def is_enabled(self,
                   feature_name,
                   context = {},
                   default_value = False):
        """
        Checks if a feature toggle is enabled.

        Notes:
        * If client hasn't been initialized yet or an error occurs, flat will default to false.

        :param feature_name: Name of the feature
        :param context: Dictionary with context (e.g. IPs, email) for feature toggle.
        :param default_value: Allows override of default value.
        :return: True/False
        """
        context.update(self.unleash_static_context)

        if self.is_initialized:
            try:
                return self.features[feature_name].is_enabled(context, default_value)
            except Exception, excep:
                LOGGER.warning(u"Returning default value for feature: %s", feature_name)
                LOGGER.warning(u"Error checking feature flag: %s", excep)
                return default_value
        else:
            LOGGER.warning(u"Returning default value for feature: %s", feature_name)
            LOGGER.warning(u"Attempted to get feature_flag %s, but client wasn't initialized!", feature_name)
            return default_value
