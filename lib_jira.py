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


def compare(field, old_value, new_value):
    if field == 'issuetype':
        #import ipdb; ipdb.set_trace()
        return new_value.get('name') == old_value.name
    return old_value == new_value


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
    data = dict(
        summary=story.title[:255],
        description=story.description,
        issuetype=dict(
            name=story.task_type,
        ),
    )
    # TODO: optmize to not update unless needed; about 4s savings per story
    to_update, data_to_update = False, {}
    for field, new_value in data.items():
        old_value = getattr(issue.fields, field)
        if not compare(field, old_value, new_value):
            to_update = True
            print '-%s: %s' % (field, old_value)
            print '+%s: %s' % (field, new_value)
            data_to_update[field] = new_value
    # need to make an edit to the record before the link is re-indexed!
    if created or to_update:
        issue.update(**data_to_update)
        if created:
            print 'Created: %s' % issue.permalink()
        else:
            print 'Updated: %s' % issue.permalink()
    else:
        print 'Nothing to update: %s' % issue.permalink()
    # see issue.fields
    # comment = jira.add_comment('JRA-1330', 'new comment')
    # jira.add_watcher(issue, 'username')
    # jira.add_attachment(issue=issue, attachment='/some/path/attachment.txt')
