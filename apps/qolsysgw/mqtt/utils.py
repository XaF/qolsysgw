import logging
import re


LOGGER = logging.getLogger(__name__)


def normalize_name_to_id(name):
    return re.compile(r'\W').sub('_', name).lower()
