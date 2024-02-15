from __future__ import absolute_import
from UnleashClient.strategies.Strategy import Strategy


class Default(Strategy):
    def apply(self, context = None):
        """
        Return true if enabled.

        :return:
        """
        return True
