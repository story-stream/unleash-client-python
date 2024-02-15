# pylint: disable=invalid-name, too-few-public-methods, use-a-generator
from __future__ import absolute_import
from datetime import datetime
from enum import Enum

from dateutil.parser import parse

from UnleashClient.utils import LOGGER, get_identifier


class ConstraintOperators(Enum):
    # Logical operators
    IN = u"IN"
    NOT_IN = u"NOT_IN"

    # String operators
    STR_ENDS_WITH = u"STR_ENDS_WITH"
    STR_STARTS_WITH = u"STR_STARTS_WITH"
    STR_CONTAINS = u"STR_CONTAINS"

    # Numeric oeprators
    NUM_EQ = u"NUM_EQ"
    NUM_GT = u"NUM_GT"
    NUM_GTE = u"NUM_GTE"
    NUM_LT = u"NUM_LT"
    NUM_LTE = u"NUM_LTE"

    # Date operators
    DATE_AFTER = u"DATE_AFTER"
    DATE_BEFORE = u"DATE_BEFORE"


class Constraint(object):
    def __init__(self, constraint_dict):
        """
        Represents a constraint on a strategy

        :param constraint_dict: From the strategy document.
        """
        self.context_name = constraint_dict[u"contextName"]
        self.operator = ConstraintOperators(
            constraint_dict[u"operator"].upper()
        )
        self.values = (
            constraint_dict[u"values"] if u"values" in constraint_dict.keys() else []
        )
        self.value = (
            constraint_dict[u"value"] if u"value" in constraint_dict.keys() else None
        )

        self.case_insensitive = (
            constraint_dict[u"caseInsensitive"]
            if u"caseInsensitive" in constraint_dict.keys()
            else False
        )
        self.inverted = (
            constraint_dict[u"inverted"]
            if u"inverted" in constraint_dict.keys()
            else False
        )

    # Methods to handle each operator type.
    def check_list_operators(self, context_value):
        return_value = False

        if self.operator == ConstraintOperators.IN:
            return_value = context_value in self.values
        elif self.operator == ConstraintOperators.NOT_IN:
            return_value = context_value not in self.values

        return return_value

    def check_string_operators(self, context_value):
        if self.case_insensitive:
            normalized_values = [x.upper() for x in self.values]
            normalized_context_value = context_value.upper()
        else:
            normalized_values = self.values
            normalized_context_value = context_value

        return_value = False

        if self.operator == ConstraintOperators.STR_CONTAINS:
            return_value = any(
                [x in normalized_context_value for x in normalized_values]
            )
        elif self.operator == ConstraintOperators.STR_ENDS_WITH:
            return_value = any(
                [normalized_context_value.endswith(x) for x in normalized_values]
            )
        elif self.operator == ConstraintOperators.STR_STARTS_WITH:
            return_value = any(
                [normalized_context_value.startswith(x) for x in normalized_values]
            )

        return return_value

    def check_numeric_operators(self, context_value):
        return_value = False

        parsed_value = float(self.value)
        parsed_context = float(context_value)

        if self.operator == ConstraintOperators.NUM_EQ:
            return_value = parsed_context == parsed_value
        elif self.operator == ConstraintOperators.NUM_GT:
            return_value = parsed_context > parsed_value
        elif self.operator == ConstraintOperators.NUM_GTE:
            return_value = parsed_context >= parsed_value
        elif self.operator == ConstraintOperators.NUM_LT:
            return_value = parsed_context < parsed_value
        elif self.operator == ConstraintOperators.NUM_LTE:
            return_value = parsed_context <= parsed_value
        return return_value

    def check_date_operators(self, context_value):
        return_value = False
        parsing_exception = False

        try:
            from dateutil.parser import ParserError

            DateUtilParserError = ParserError
        except ImportError:
            DateUtilParserError = ValueError

        try:
            parsed_date = parse(self.value)
            if isinstance(context_value, unicode):
                context_date = parse(context_value)
            else:
                context_date = context_value
        except DateUtilParserError:
            LOGGER.error(u"Unable to parse date: {}".format(self.value))
            parsing_exception = True

        if not parsing_exception:
            if self.operator == ConstraintOperators.DATE_AFTER:
                return_value = context_date > parsed_date
            elif self.operator == ConstraintOperators.DATE_BEFORE:
                return_value = context_date < parsed_date

        return return_value

    def apply(self, context = None):
        """
        Returns true/false depending on constraint provisioning and context.

        :param context: Context information
        :return:
        """
        constraint_check = False

        try:
            context_value = get_identifier(self.context_name, context)

            # Set currentTime if not specified
            if self.context_name == u"currentTime" and not context_value:
                context_value = datetime.now()

            if context_value is not None:
                if self.operator in [
                    ConstraintOperators.IN,
                    ConstraintOperators.NOT_IN,
                ]:
                    constraint_check = self.check_list_operators(
                        context_value=context_value
                    )
                elif self.operator in [
                    ConstraintOperators.STR_CONTAINS,
                    ConstraintOperators.STR_ENDS_WITH,
                    ConstraintOperators.STR_STARTS_WITH,
                ]:
                    constraint_check = self.check_string_operators(
                        context_value=context_value
                    )
                elif self.operator in [
                    ConstraintOperators.NUM_EQ,
                    ConstraintOperators.NUM_GT,
                    ConstraintOperators.NUM_GTE,
                    ConstraintOperators.NUM_LT,
                    ConstraintOperators.NUM_LTE,
                ]:
                    constraint_check = self.check_numeric_operators(
                        context_value=context_value
                    )
                elif self.operator in [
                    ConstraintOperators.DATE_AFTER,
                    ConstraintOperators.DATE_BEFORE,
                ]:
                    constraint_check = self.check_date_operators(
                        context_value=context_value
                    )
            # This is a special case in the client spec - so it's getting it's own handler here
            elif self.operator is ConstraintOperators.NOT_IN:  # noqa: PLR5501
                constraint_check = True

        except Exception as excep:  # pylint: disable=broad-except
            LOGGER.info(
                u"Could not evaluate context %s!  Error: %s", self.context_name, excep
            )

        return not constraint_check if self.inverted else constraint_check
