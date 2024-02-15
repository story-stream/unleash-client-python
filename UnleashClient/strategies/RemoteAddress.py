from __future__ import absolute_import
import ipaddress
from UnleashClient.strategies.Strategy import Strategy
from UnleashClient.utils import LOGGER


class RemoteAddress(Strategy):
    def load_provisioning(self):
        parsed_ips = []

        for address in self.parameters[u"IPs"].split(u','):

            if u"/" in address:
                try:
                    parsed_ips.append(ipaddress.ip_network(address.strip(), strict=True))  # type: ignore
                except (ipaddress.AddressValueError, ipaddress.NetmaskValueError, ValueError) as parsing_error:
                    LOGGER.warning(u"Error parsing IP range: %s", parsing_error)
            else:
                try:
                    parsed_ips.append(ipaddress.ip_address(address.strip()))  # type: ignore
                except (ipaddress.AddressValueError, ipaddress.NetmaskValueError, ValueError) as parsing_error:
                    LOGGER.warning(u"Error parsing IP : %s", parsing_error)

        return parsed_ips

    def apply(self, context = None):
        """
        Returns true if IP is in list of IPs

        :return:
        """
        return_value = False

        try:
            context_ip = ipaddress.ip_address(context[u"remoteAddress"])
        except (ipaddress.AddressValueError, ipaddress.NetmaskValueError, ValueError) as parsing_error:
            LOGGER.warning(u"Error parsing IP : %s", parsing_error)
            context_ip = None

        if context_ip:
            for addr_or_range in [value for value in self.parsed_provisioning if value.version == context_ip.version]:
                if isinstance(addr_or_range, (ipaddress.IPv4Address, ipaddress.IPv6Address)):
                    if context_ip == addr_or_range:
                        return_value = True
                        break
                else:
                    if context_ip in addr_or_range:
                        return_value = True
                        break

        return return_value
