import argparse

import lib_jira
import lib_phab
from model import Story
import settings
import labels


def kwargs_or_default(setting_value):
    if setting_value:
        return dict(default=setting_value)
    return dict(required=True)


def auth(args):
    lib_jira.test_auth(
        server=args.server,
        username=args.username,
        password=args.password)
    lib_jira.save_credentials()


def doctor(args):
    lib_jira.test_auth()


def projects(args):
    lib_phab.list_projects(args.query)


def query(args):
    total_results = 0
    for task in lib_phab.query_project(args.project):
        story = Story.from_phab(task)
        print story
        total_results += 1
    print 'Total %s' % total_results

def _sync_one(phid, jira_project, update_comments=False):
    # TODO: move to function in lib_phab
    if phid.startswith('T'):
        phid = int(phid[1:])
    task = lib_phab.get_task(phid)
    story = Story.from_phab(task)
    print story
    # pre-processing
    label_whitelist = settings.MIGRATE_ONLY_ISSUES_WITH_LABELS
    if label_whitelist:
        if not labels.one_label_in_set(story.labels, label_whitelist):
            print 'Skipping, issues does not have labels: %s' % label_whitelist
            return None, False
    label_blacklist = settings.NO_MIGRATE_ISSUES_WITH_LABELS
    if label_blacklist:
        if labels.one_label_in_set(story.labels, label_blacklist):
            print 'Skipping, issues DOES have one of labels: %s' % label_blacklist
            return None, False
    # jira_issue = Story.to_jira(story)
    # print jira_issue
    issue, created = lib_jira.create_or_update(jira_project, story)
    if created or update_comments:
        # this is relatively expensive, so only do it the first time
        comments = lib_phab.get_comments(phid)
        lib_jira.update_comments(issue, comments)
    if created:
        lib_phab.add_backlink_comment(phid, issue.permalink())
    return issue, created


def sync(args):
    phid = args.phid or None
    if args.jira:
        remote_links = lib_jira.get_issue_remote_links(args.jira)
        for remote_link in remote_links:
            if remote_link.object.url.startswith(settings.PHAB_BASE_URL):
                phid = remote_link.object.url.split('/')[-1]
        if not phid:
            raise Exception('Could not find remote link from: %s' % args.jira)
    if not phid:
        raise Exception('You need to specify either --phid or --jira')
    _sync_one(phid, args.jira_project, args.update_comments)


def sync_all(args):
    success, skipped = 0, 0
    for task in lib_phab.query_project(args.project):
        story = Story.from_phab(task)
        if args.offset and skipped < int(args.offset):
            skipped += 1
            continue
        if settings.ISSUES_TO_SKIP and story.phid in settings.ISSUES_TO_SKIP:
            continue
        _sync_one(story.phid, args.jira_project, args.update_comments)
        success += 1
        if args.limit and success >= int(args.limit):
            break
    print 'Total %s' % success


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='phab2jira')
    subparsers = parser.add_subparsers(help='sub-command help')

    parser_auth = subparsers.add_parser('auth', help='Authenticate to JIRA')
    parser_auth.add_argument('--server', help='JIRA Server URL',
        **kwargs_or_default(settings.JIRA_BASE_URL))
    parser_auth.add_argument('--username', help='JIRA username',
        **kwargs_or_default(settings.JIRA_USERNAME))
    parser_auth.add_argument('--password', help='JIRA password',
        **kwargs_or_default(settings.JIRA_PASSWORD))
    parser_auth.set_defaults(func=auth)

    parser_doctor = subparsers.add_parser('doctor', help='Run some diagnostics')
    parser_doctor.set_defaults(func=doctor)

    parser_projects = subparsers.add_parser('projects',
        help='List phabricator projects')
    parser_projects.add_argument('--query', help='Full text search query',
        required=True)
    parser_projects.set_defaults(func=projects)

    parser_query = subparsers.add_parser('query',
        help='Query issues in a project')
    parser_query.add_argument('--project', help='Phabricator project to list',
        **kwargs_or_default(settings.PHAB_DEFAULT_PROJECT))
    parser_query.set_defaults(func=query)

    parser_sync = subparsers.add_parser('sync',
        help='Sync ONE issue from Phabricator to JIRA')
    parser_sync.add_argument('--phid',
        help='Phabricator ID of issue to sync')
    parser_sync.add_argument('--jira',
        help='JIRA ID ofissue to re-sync')
    parser_sync.add_argument('--jira-project',
        help='JIRA project to create the issue in',
        **kwargs_or_default(settings.JIRA_DEFAULT_PROJECT))
    parser_sync.add_argument('--update-comments', action='store_true',
        help='Update comments EVERY time')
    parser_sync.set_defaults(func=sync)

    parser_sync_all = subparsers.add_parser('sync-all',
        help='Sync ALL issues from a Phabricator project to JIRA')
    parser_sync_all.add_argument('--project', help='Project to sync from',
        **kwargs_or_default(settings.PHAB_DEFAULT_PROJECT))
    parser_sync_all.add_argument('--jira-project',
        help='JIRA project to create the issue in',
        **kwargs_or_default(settings.JIRA_DEFAULT_PROJECT))
    parser_sync_all.add_argument('--update-comments', action='store_true',
        help='Update comments EVERY time')
    parser_sync_all.add_argument('--limit', action='store',
        help='Stop after a certiain number of issues')
    parser_sync_all.add_argument('--offset', action='store',
        help='Start after a certiain number of issues')
    parser_sync_all.set_defaults(func=sync_all)

    args = parser.parse_args()
    args.func(args)
