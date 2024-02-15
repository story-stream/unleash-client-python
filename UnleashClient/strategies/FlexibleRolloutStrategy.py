from __future__ import absolute_import
import random
from UnleashClient.strategies.Strategy import Strategy
from UnleashClient.utils import normalized_hash


class FlexibleRollout(Strategy):
    @staticmethod
    def random_hash():
        return random.randint(1, 100)

    def apply(self, context = None):
        """
        If constraints are satisfied, return a percentage rollout on provisioned.

        :return:
        """
        percentage = int(self.parameters[u'rollout'])
        activation_group = self.parameters[u'groupId']
        stickiness = self.parameters[u'stickiness']

        if stickiness == u'default':
            if u'userId' in context.keys():
                calculated_percentage = normalized_hash(context[u'userId'], activation_group)
            elif u'sessionId' in context.keys():
                calculated_percentage = normalized_hash(context[u'sessionId'], activation_group)
            else:
                calculated_percentage = self.random_hash()
        elif stickiness in [u'userId', u'sessionId']:
            calculated_percentage = normalized_hash(context[stickiness], activation_group)
        else:
            # This also handles the stickiness == random scenario.
            calculated_percentage = self.random_hash()

        return percentage > 0 and calculated_percentage <= percentage
