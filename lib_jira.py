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


def create_or_update(project, story):
    # jira.createmeta for other required fields
    jira = _connect()
    created = True
    matching_issues = jira.search_issues("""
        project = %s
        AND issueFunction in linkedIssuesOfRemote("%s")""" % (
            project, story.phab_url))
    if len(matching_issues) == 1:
        issue = matching_issues[0]
        created = False
    elif len(matching_issues) > 1:
        raise ValueError(
            'Found more than one issue with a remote link %s' % story.phab_url)
    else:
        issue = jira.create_issue(
            project=project,
            summary=story.title[:255],
            description='Syncing from Phabricator...',
            issuetype=dict(
                name=story.task_type,
            ),
        )
        jira.add_simple_link(issue, dict(
            url=story.phab_url,
            title=story.phab_title))
    # need to make an edit to the record before the link is re-indexed!
    issue.update(
        summary=story.title[:255],
        description=story.description,
        issuetype=dict(
            name=story.task_type,
        ),
    )
    if created:
        print 'Created: %s' % issue.permalink()
    else:
        print 'Updated: %s' % issue.permalink()
    # see issue.fields
    # comment = jira.add_comment('JRA-1330', 'new comment')
    # jira.add_watcher(issue, 'username')
    # jira.add_attachment(issue=issue, attachment='/some/path/attachment.txt')
