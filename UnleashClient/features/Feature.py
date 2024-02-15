from __future__ import absolute_import
from UnleashClient.utils import LOGGER


# pylint: disable=dangerous-default-value, broad-except
class Feature(object):
    def __init__(self,
                 name,
                 enabled,
                 strategies):
        """
        An representation of a fewature object

        :param name: Name of the feature.
        :param enabled: Whether feature is enabled.
        :param strategies: List of sub-classed Strategy objects representing feature strategies.
        """
        # Experiment information
        self.name = name
        self.enabled = enabled
        self.strategies = strategies

        # Stats tracking
        self.yes_count = 0
        self.no_count = 0

    def reset_stats(self):
        """
        Resets stats after metrics reporting

        :return:
        """
        self.yes_count = 0
        self.no_count = 0

    def increment_stats(self, result):
        """
        Increments stats.

        :param result:
        :return:
        """
        if result:
            self.yes_count += 1
        else:
            self.no_count += 1

    def is_enabled(self,
                   context = None,
                   default_value = False):
        """
        Checks if feature is enabled.

        :param context: Context information
        :param default_value: Optional, but allows for override.
        :return:
        """
        flag_value = default_value

        if self.enabled:
            try:
                strategy_result = any([x.execute(context) for x in self.strategies])
                flag_value = flag_value or strategy_result
            except Exception as strategy_except:
                LOGGER.warning(u"Error checking feature flag: %s", strategy_except)

        self.increment_stats(flag_value)

        LOGGER.info(u"Feature toggle status for feature %s: %s", self.name, flag_value)

        return flag_value
