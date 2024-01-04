import logging
import re
import unicodedata


LOGGER = logging.getLogger(__name__)


def rmdiacritics(char):
    '''
    Return the base character of char, by "removing" any
    diacritics like accents or curls and strokes and the like.

    Taken from https://stackoverflow.com/a/15547803
    '''
    desc = unicodedata.name(char)
    cutoff = desc.find(' WITH ')
    if cutoff != -1:
        desc = desc[:cutoff]
        try:
            char = unicodedata.lookup(desc)
        except KeyError:
            pass  # removing "WITH ..." produced an invalid name
    return char


def normalize_name_to_id(name):
    ascii_name = ''.join([rmdiacritics(c) for c in name])
    clean_name = re.sub(r'[^a-zA-Z0-9_]', '_', ascii_name)
    return clean_name.lower()
