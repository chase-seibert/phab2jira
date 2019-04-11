import argparse

import lib_jira
import lib_phab
from model import Story
import settings


def kwargs_or_default(setting_value):
    if setting_value:
        return dict(default=setting_value)
    return dict(required=True)


def auth(args):
    lib_jira.test_auth(**args.__dict__)
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


def sync(args):
    if args.phid:
        phid = args.phid
        # TODO: move to function in lib_phab
        if phid.startswith('T'):
            phid = int(phid[1:])
        task = lib_phab.get_task(phid)
        story = Story.from_phab(task)
        print story
        # jira_issue = Story.to_jira(story)
        # print jira_issue
        issue, created = lib_jira.create_or_update(args.project, story)
        if created or args.update_comments:
            # this is relatively expensive, so only do it the first time
            comments = lib_phab.get_comments(phid)
            lib_jira.update_comments(issue, comments)


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
    parser_query.add_argument('--project', help='Project to list',
        **kwargs_or_default(settings.PHAB_DEFAULT_PROJECT))
    parser_query.set_defaults(func=query)

    parser_sync = subparsers.add_parser('sync',
        help='Sync issues from Phabricator to JIRA')
    parser_sync.add_argument('--phid',
        help='Phabricator ID of ONE issue to sync')
    parser_sync.add_argument('--project', help='Project to create the issue in',
        **kwargs_or_default(settings.JIRA_DEFAULT_PROJECT))
    parser_sync.add_argument('--update-comments', action='store_true',
        help='Update comments EVERY time')
    parser_sync.set_defaults(func=sync)

    args = parser.parse_args()
    args.func(args)
