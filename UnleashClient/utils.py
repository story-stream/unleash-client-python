from __future__ import absolute_import
import logging
import sys
import mmh3  # pylint: disable=import-error

LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(logging.StreamHandler(sys.stdout))

def normalized_hash(identifier,
                    activation_group):
    return mmh3.hash(u"{}:{}".format(activation_group, identifier), signed=False) % 100 + 1


def get_identifier(context_key_name, context):
    if context_key_name in context.keys():
        value = context[context_key_name]
    elif (
        u"properties" in context.keys()
        and context_key_name in context[u"properties"].keys()
    ):
        value = context[u"properties"][context_key_name]
    else:
        value = None

    return value
