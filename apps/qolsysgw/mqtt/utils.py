import logging
import re
import subprocess


LOGGER = logging.getLogger(__name__)


def get_mac_from_host(ip_or_host):
    try:
        # The arp command will automatically resolve the hostname to an
        # IP address for us if needed
        process = subprocess.run(['arp', ip_or_host], capture_output=True)
    except subprocess.SubprocessError:
        LOGGER.exception(f"Error trying to get the mac address for '{ip_or_host}'")
        return None

    output = process.stdout.decode('utf-8')

    m = re.search(r'(([a-f\d]{1,2}:){5}[a-f\d]{1,2})', output)

    if m is None:
        LOGGER.warning(f"No mac address found for '{ip_or_host}'")
        return None

    mac = m[0]
    LOGGER.debug(f"Found mac address '{mac}' for '{ip_or_host}'")
    return mac
