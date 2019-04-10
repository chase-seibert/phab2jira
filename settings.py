PHAB_BASE_URL = 'https://secure.phabricator.com'
PHAB_DEFAULT_PROJECT = None

JIRA_BASE_URL = 'https://jira.atlassian.com'
JIRA_USERNAME = None
JIRA_PASSWORD = None
JIRA_DEFAULT_PROJECT = None  # can be either Project ID or Key (letters)
JIRA_STORY_POINTS_FIELD = None

PHAB_TO_JIRA_PRIORITY_MAP = {
    'Unbreak Now!': 'Highest',
    'Needs Triage': 'Low',
    'Blocker!': 'Highest',
    'High': 'High',
    'Normal': 'Medium',
    'Low': 'Low',
    'Wishlist': 'Lowest',
}


def get_story_points(obj):
    return int(obj['fields']['points'])


FIELD_MAPS = {
    # 'customfield_10006': get_story_points,
}


# allow custom over rides NOT checked in to git (in .gitignore)
# to use, create a settings_override.py file and duplicate the
# subset of settings you wish to over-ride there
try:
    from settings_override import *
except ImportError:
    pass
