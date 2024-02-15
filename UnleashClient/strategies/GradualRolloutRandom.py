from __future__ import absolute_import
import random
from UnleashClient.strategies.Strategy import Strategy


class GradualRolloutRandom(Strategy):
    def apply(self, context = None):
        """
        Returns random assignment.

        :return:
        """
        percentage = int(self.parameters[u"percentage"])

        return percentage > 0 and random.randint(1, 100) <= percentage
