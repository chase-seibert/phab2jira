import argparse

import lib_jira
import lib_phab
from model import Story


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
        if phid.startswith('T'):
            phid = phid[1:]
        task = lib_phab.get_task(phid)
        story = Story.from_phab(task)
        print story


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='phab2jira')
    subparsers = parser.add_subparsers(help='sub-command help')

    parser_auth = subparsers.add_parser('auth', help='Authenticate to JIRA')
    parser_auth.add_argument('--server', help='JIRA Server URL', required=True)
    parser_auth.add_argument('--username', help='JIRA username', required=True)
    parser_auth.add_argument('--password', help='JIRA password', required=True)
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
        required=True)
    parser_query.set_defaults(func=query)

    parser_sync = subparsers.add_parser('sync',
        help='Sync issues from Phabricator to JIRA')
    parser_sync.add_argument('--phid',
        help='Phabricator ID of ONE issue to sync')
    parser_sync.set_defaults(func=sync)

    args = parser.parse_args()
    args.func(args)
