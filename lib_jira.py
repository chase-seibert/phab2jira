import pprint
import stat
import os
import json

from jira import JIRA

import settings

# See: https://jira.readthedocs.io/en/master/api.html

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
    if type(new_value) == dict and 'name' in new_value:
        if hasattr(old_value, 'name'):
            return new_value.get('name') == old_value.name
    if field == 'labels':
        return sorted(old_value) == sorted(new_value)
    if field == 'description' and old_value is None and new_value == '':
        return True
    return old_value == new_value


def get_issue_remote_links(issue_id):
    jira = _connect()
    issue = jira.issue(issue_id)
    return jira.remote_links(issue)


def find_issue_by_remote_url(project, remote_url):
    jira = _connect()
    created = True
    matching_issues = jira.search_issues("""
        project = %s
        AND issueFunction in linkedIssuesOfRemote("%s")""" % (
            project, remote_url))
    if len(matching_issues) > 1:
        raise ValueError(
            'Found more than one issue with a remote link %s' % story.phab_url)
    elif len(matching_issues) == 1:
        issue = matching_issues[0]
        return issue
    return None


def _create_or_update_issue(project, story, epic_id=None):
    # See: https://developer.atlassian.com/server/jira/platform/jira-rest-api-examples/#creating-an-issue-examples
    jira = _connect()
    created = True
    issue = find_issue_by_remote_url(project, story.phab_url)
    if issue:
        created = False
    else:
        # create a placeholder issue, with the right type
        # jira.createmeta for other required fields
        kwargs = story.to_jira(fields=['summary', 'issuetype'])
        if epic_id:
            if not settings.JIRA_EPIC_FIELD:
                raise Exception('No JIRA_EPIC_FIELD setting defined')
            kwargs[settings.JIRA_EPIC_FIELD] = epic_id
        issue = jira.create_issue(
            project=project,
            description='Syncing from Phabricator...',
            **kwargs)
        # create a remote link back to phab, used to look this item up later
        jira.add_simple_link(issue, dict(
            url=story.phab_url,
            title=story.phab_title))
    return issue, created


def update_status(issue, new_status):
    jira = _connect()
    if issue.fields.status.name.lower() == new_status.lower():
        return
    for transition in jira.transitions(issue):
        transistion_id = transition['id']
        transistion_name = transition['name']
        if transistion_name.lower() == new_status.lower():
            print '+status: %s (%s)' % (transistion_id, transistion_name)
            jira.transition_issue(issue, transistion_id)
            return
    raise NotImplementedError('Status "%s" not found' % new_status)


def update_comments(issue, comments):
    from model import Story
    jira = _connect()
    existing_comments = jira.comments(issue)
    existing_comments_text = [c.body for c in existing_comments]
    # list starts with most recent first, but want to insert the OLDest first,
    # so that it matches the order in JIRA of natural comments
    list.reverse(comments)
    for new_comment in comments:
        comment_text = Story.get_comment_text(new_comment)
        # don't add dupes, comment updating not implemented
        if comment_text in existing_comments_text:
            continue
        jira.add_comment(issue, comment_text)
        print '+comment: %s' % (
            repr(comment_text[:72] + '...') if len(comment_text) > 72 else repr(comment_text))


def create_or_update(project, story, epic_id=None):
    jira = _connect()
    issue, created = _create_or_update_issue(project, story, epic_id)
    # import ipdb; ipdb.set_trace()
    data = story.to_jira()
    # optmize to not update unless needed; about 4s savings per story
    to_update, data_to_update = False, {}
    for field, new_value in data.items():
        old_value = getattr(issue.fields, field)
        if not compare(field, old_value, new_value):
            to_update = True
            # print a diff of what's changing
            print '-%s: %s' % (field, old_value)
            print '+%s: %s' % (field, new_value)
            data_to_update[field] = new_value
    update_status(issue, story.status)
    if created or to_update:
        # need to make an edit to the record before the link is re-indexed!
        issue.update(**data_to_update)
        if created:
            print 'Created: %s' % issue.permalink()
        else:
            print 'Updated: %s' % issue.permalink()
    else:
        print 'Nothing to update: %s' % issue.permalink()
    # comment = jira.add_comment('JRA-1330', 'new comment')
    # jira.add_watcher(issue, 'username')
    # jira.add_attachment(issue=issue, attachment='/some/path/attachment.txt')
    return issue, created


def add_backlink_comment(issue, phid, phab_url):
    jira = _connect()
    jira.add_comment(issue, """#Maniphest: %s
Tracked in Maniphest by %s
""" % (phid, phab_url))
