"""Configuration parameters for the package."""

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

from os.path import expanduser, join, abspath, dirname

from future import standard_library
standard_library.install_aliases()

from os import getenv
from pprint import pprint
from requests import get

GOOGLE_OAUTH_CLIENT_ID = getenv('GOOGLE_OAUTH_CLIENT_ID')
GOOGLE_OAUTH_CLIENT_SECRET = getenv('GOOGLE_OAUTH_CLIENT_ID')
GOOGLE_API_URL = 'https://accounts.google.com/o/oauth2/auth'
SCOPE = ['https://www.googleapis.com/auth/userinfo.email',
         'https://www.googleapis.com/auth/userinfo.profile']


USER_CONFIG_DIR = join(expanduser('~'), '.gobble')
TOKEN_FILEPATH = join(USER_CONFIG_DIR, 'token')

ASSETS_DIR = abspath(join(dirname(__file__), '..', 'assets'))
EXAMPLES_DIR = abspath(join(ASSETS_DIR, 'examples'))

OS_HOST = 'next.openspending.org'
OS_PORT = None

SCHEMAS_HOST = 'http://schemas.datapackages.org/'
FISCAL_SCHEMA = get(SCHEMAS_HOST + 'fiscal-data-package.json').json()
DATAPACKAGE_SCHEMA = get(SCHEMAS_HOST + 'data-package.json').json()
TABULAR_SCHEMA = get(SCHEMAS_HOST + 'tabular-data-package.json').json()
SCHEMA_DETECTION_THRESHOLD = 0.5

if __name__ == '__main__':
    pprint({k: v for k, v in locals().items() if k == k.upper()})
