EMAIL_DOMAIN_SUFFIX = '@domain.com'

PHAB_BASE_URL = 'https://secure.phabricator.com'
PHAB_DEFAULT_PROJECT = None
PHAB_ISSUE_TYPE_FIELD = None

JIRA_BASE_URL = 'https://jira.atlassian.com'
JIRA_USERNAME = None
JIRA_PASSWORD = None
JIRA_DEFAULT_PROJECT = None  # can be either Project ID or Key (letters)
JIRA_STORY_POINTS_FIELD = None
JIRA_EPIC_FIELD = None

PHAB_TO_JIRA_PRIORITY_MAP = {
    'Unbreak Now!': 'Highest',
    'Needs Triage': 'Low',
    'Blocker!': 'Highest',
    'High': 'High',
    'Normal': 'Medium',
    'Low': 'Low',
    'Wishlist': 'Lowest',
}


JIRA_DEFAULT_STATUS = 'Open'
PHAB_TO_JIRA_STATUS_MAP = {
    'Open': 'open',
    'Resolved': 'done',
    'Needs Investigation': 'on hold',
    'In progress': 'in progress',
    'Verify Fix': 'in review',
}

def get_story_points(obj):
    return int(obj['fields']['points'])


FIELD_MAPS = {
    # 'customfield_10006': get_story_points,
}

# only migrate a subset of the issues matching your query
MIGRATE_ONLY_ISSUES_WITH_LABELS = None

# you can skip migrating issues with specific labels, usful if there is a
# subset of your query you do NOT want to migrate to JIRA
NO_MIGRATE_ISSUES_WITH_LABELS = [
    #'foobar',
]

# don't migrate references to these users
BLACKLISTED_USERS = [
    # 'foo@bar.com'
]

ISSUES_TO_SKIP = []

# allow custom over rides NOT checked in to git (in .gitignore)
# to use, create a settings_override.py file and duplicate the
# subset of settings you wish to over-ride there
try:
    from settings_override import *
except ImportError:
    pass
