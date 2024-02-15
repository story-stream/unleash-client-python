from __future__ import absolute_import
from fcache.cache import FileCache
from UnleashClient.features import Feature
from UnleashClient.constants import FEATURES_URL
from UnleashClient.utils import LOGGER


# pylint: disable=broad-except
def _create_strategies(provisioning,
                       strategy_mapping):
    feature_strategies = []

    for strategy in provisioning[u"strategies"]:
        try:
            if u"parameters" in strategy.keys():
                strategy_provisioning = strategy[u'parameters']
            else:
                strategy_provisioning = {}

            if u"constraints" in strategy.keys():
                constraint_provisioning = strategy[u'constraints']
            else:
                constraint_provisioning = {}

            feature_strategies.append(strategy_mapping[strategy[u'name']](constraints=constraint_provisioning, parameters=strategy_provisioning))
        except Exception as excep:
            LOGGER.warning(u"Failed to load strategy.  This may be a problem with a custom strategy.  Exception: %s",
                           excep)

    return feature_strategies


def _create_feature(provisioning,
                    strategy_mapping):
    if u"strategies" in provisioning.keys():
        parsed_strategies = _create_strategies(provisioning, strategy_mapping)
    else:
        parsed_strategies = []

    return Feature(name=provisioning[u"name"],
                   enabled=provisioning[u"enabled"],
                   strategies=parsed_strategies)


def load_features(cache,
                  feature_toggles,
                  strategy_mapping):
    """
    Caching

    :param cache: Should be the cache class variable from UnleashClient
    :param feature_toggles: Should be the features class variable from UnleashClient
    :return:
    """
    # Pull raw provisioning from cache.
    try:
        feature_provisioning = cache[FEATURES_URL]

        # Parse provisioning
        parsed_features = {}
        feature_names = [d[u"name"] for d in feature_provisioning[u"features"]]

        for provisioning in feature_provisioning[u"features"]:
            parsed_features[provisioning[u"name"]] = provisioning

        # Delete old features/cache
        for feature in list(feature_toggles.keys()):
            if feature not in feature_names:
                del feature_toggles[feature]

        # Update existing objects
        for feature in feature_toggles.keys():
            feature_for_update = feature_toggles[feature]
            strategies = parsed_features[feature][u"strategies"]

            feature_for_update.enabled = parsed_features[feature][u"enabled"]
            if strategies:
                parsed_strategies = _create_strategies(parsed_features[feature], strategy_mapping)
                feature_for_update.strategies = parsed_strategies

        # Handle creation or deletions
        new_features = list(set(feature_names) - set(feature_toggles.keys()))

        for feature in new_features:
            feature_toggles[feature] = _create_feature(parsed_features[feature], strategy_mapping)
    except KeyError as cache_exception:
        LOGGER.warning(u"Cache Exception: %s", cache_exception)
        LOGGER.warning(u"Unleash client does not have cached features.  Please make sure client can communicate with Unleash server!")
