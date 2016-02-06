import argparse
import json
import pprint
import sys
import urllib
import urllib2

import oauth2


API_HOST = 'api.yelp.com'
DEFAULT_TERM = 'dinner'
DEFAULT_LOCATION = 'San Francisco, CA'
SEARCH_LIMIT = 20
SEARCH_PATH = '/v2/search/'
BUSINESS_PATH = '/v2/business/'

# OAuth credential placeholders that must be filled in by users.
CONSUMER_KEY = dStcfiGFCoZkOlva9XeZtA
CONSUMER_SECRET = WoJ9LxTFCVgdYFq6yn3GAlLRRXE
TOKEN = VnMH3YjeyYcvV4mhXVzfcJhOwRNgaBFX
TOKEN_SECRET = boGGX7K0aX2gcY39kF3uAwuEdu0