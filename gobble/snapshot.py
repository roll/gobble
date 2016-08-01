"""This module has good intentions, like helping you debug API calls"""


from collections import OrderedDict
from copy import deepcopy
from datetime import datetime
from json import loads
from os import listdir
from os.path import join, isdir
from re import search

import io

from gobble.logger import log
from gobble.utilities import wopen23, dumps23, to_json
from gobble.configuration import settings, SNAPSHOTS_DIR


class SnapShot(OrderedDict):
    """A chatty wrapper around the API transaction

    In freeze mode, the snapshot gets stripped of its secrets
    and saved inside the repo. So freeze mode is a cheap way
    to generate (quasi) specs for the API.
    """
    def __init__(self, endpoint, url, reponse, params,
                 headers=None, json=None, is_freeze=False):
        """Log, record and save before returning an instance"""

        self.is_freeze = is_freeze

        self.url = url
        self.endpoint = endpoint
        self.response = reponse
        self.headers = headers
        self.params = params
        self.request_payload = json

        super(OrderedDict, self).__init__(self._template)
        self.timestamp = str(datetime.now())

        self._log()
        self._record()
        self._save()

    def _log(self):
        """Is there such a thing as too much logging?"""

        code = self.response.status_code
        reason = self.response.reason
        response_json = to_json(self.response)
        begin = code, reason, self.endpoint, 'begin'
        end = code, reason, self.endpoint, 'end'
        transaction = ' [%s] %s - %s (%s) '

        log.debug('{:*^100}'.format(transaction % begin))

        messages = (
            ('Request endpoint: %s', self.endpoint.url),
            ('Request time: %s', self.response.elapsed),
            ('Request parameters: %s', self.params),
            ('Request payload: %s', self.request_payload),
            ('Request headers: %s', self.headers),
            ('Response headers: %s', self.response.headers),
            ('Response payload: %s', response_json),
            ('Response cookies: %s', self.response.cookies),
            ('Request full URL: %s', self.url),
        )
        for message in messages:
            log.debug(*message)

        if settings.EXPANDED_LOG_STYLE:
            log.debug(dumps23(response_json))

        log.debug('{:*^100}'.format(transaction % end))

    def _record(self):
        """Store the transaction info"""

        json = to_json(self.response)
        duplicate_json = deepcopy(json)

        if settings.FREEZE_MODE:
            freeze(duplicate_json)

        self['timestamp'] = self.timestamp
        self['url'] = self.url
        self['query'] = self.params
        self['request_json'] = self.request_payload
        self['response_json'] = duplicate_json
        self['request_headers'] = self.headers
        self['response_headers'] = dict(self.response.headers)
        self['cookies'] = dict(self.response.cookies)

    @property
    def _template(self):
        return (
            ('timestamp', None),
            ('host', settings.OS_URL),
            ('url', None),
            ('method', self.endpoint.method),
            ('path', self.endpoint.path),
            ('query', None),
            ('request_json', None),
            ('response_json', None),
            ('request_headers', None),
            ('response_headers', None),
            ('cookies', None),
        )

    def _save(self):
        """Save the snapshot as JSON in the appropriate place"""
        with wopen23(self._filepath) as file:
            file.write(dumps23(self))
        log.debug('Saved request + response to %s', self._filepath)

    @property
    def _folder(self):
        return SNAPSHOTS_DIR if self.is_freeze else settings.USER_DIR

    @property
    def _filepath(self):
        template = '{method}.{path}.json'
        dot_path = '.'.join(self.endpoint._path).rstrip('/')
        params = {'method': self.endpoint.method, 'path': dot_path}
        filename = template.format(**params)
        return join(self._folder, filename)

    def __str__(self):
        return str(self.endpoint) + ' at ' + self.timestamp

    def __repr__(self):
        return '<SnapShot %s>' % str(self)

    @property
    def json(self):
        return dumps23(self)


def freeze(json):
    """Recursively substitute unwanted strings inside a json-like object

    Basically, remove anything in the substitution list below, even when
    hidden in inside query strings.
    """
    subs = {
        'jwt': r'jwt=([^&^"]+)',
        "bucket_id": r'\/([\w]{32})\/',
        'Signature': r'Signature=([^&^"]+)',
        'AWSAccessKeyId': r'AWSAccessKeyId=([^&^"]+)',
        'Expires': r'Expires=([^&^"]+)',
        'Date': None,
        "Set-Cookie": None,
        'token': None,
    }

    def regex(dummy_, json_, key_, pattern_, value_):
        match = search(pattern_, value_)
        if match:
            sub = match.group(1), dummy_
            json_[key_] = value_.replace(*sub)

    if isinstance(json, list):
        for item in json:
            freeze(item)
    elif isinstance(json, dict):
        for field, pattern in subs.items():
            for key, value in json.items():
                dummy = field.upper()
                if key == field:
                    json[key] = dummy
                elif isinstance(value, str):
                    if pattern:
                        regex(dummy, json, key, pattern, value)
                elif isinstance(value, dict):
                    freeze(value)


def freeze_and_archive(destination):
    """Freeze and move all snapshots to the destination folder."""

    if not isdir(destination):
        raise NotADirectoryError(destination)

    for file in listdir(settings.USER_DIR):
        verb = file.split('.')[0]
        if verb in ['GET', 'POST', 'PUT']:

            with io.open(file) as in_:
                snapshot = loads(in_.read())

            freeze(snapshot)

            # Overwtite if necessary
            with wopen23(join(destination, file)) as out:
                out.write(dumps23(snapshot))