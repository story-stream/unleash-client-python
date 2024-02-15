from __future__ import absolute_import
from UnleashClient.utils import normalized_hash
from UnleashClient.strategies.Strategy import Strategy


class GradualRolloutSessionId(Strategy):
    def apply(self, context = None):
        """
        Returns true if userId is a member of id list.

        :return:
        """
        percentage = int(self.parameters[u"percentage"])
        activation_group = self.parameters[u"groupId"]

        return percentage > 0 and normalized_hash(context[u"sessionId"], activation_group) <= percentage
