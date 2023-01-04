from callee.strings import Regex

# Representation of an ISO date so we can match against it
ISODATE = Regex(r'^[0-9]{4}-[0-9]{2}-[0-9]{2}T'
                r'[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{6}'
                r'\+00:00$')
