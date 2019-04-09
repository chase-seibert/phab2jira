import pprint
import stat
import os
import json

from jira import JIRA


RC_FILE = os.path.join(os.path.expanduser('~'), '.jirarc')
_credentials = {}


def _connect(**kwargs):
    global _credentials
    _credentials = kwargs or load_credentials()
    return JIRA(_credentials['server'],
        auth=(_credentials['username'], _credentials['password']))


def test_auth(**kwargs):
    jira = _connect(**kwargs)
    server_info = jira.server_info()
    print 'Successfully connected to: %s' % server_info['baseUrl']
    print 'Version: %s' % server_info['version']
    print 'Connected as: %s' % jira.user(_credentials['username'])


def save_credentials():
    with open(RC_FILE, 'w+', stat.S_IRUSR | stat.S_IWUSR) as _file:
        _file.write(json.dumps({
            'server': _credentials['server'],
            'username': _credentials['username'],
            'password': _credentials['password'],
        }))
    print 'Wrote credentials to %s' % RC_FILE


def load_credentials():
    try:
        with open(RC_FILE, 'r') as _file:
            credentials = json.load(_file)
            assert type(_credentials) == dict
            return credentials
    except IOError as e:
        print e
        exit(1)
