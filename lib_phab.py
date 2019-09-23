from datetime import datetime

from phabricator import Phabricator

import cache
import settings


def phid_to_name(phid):
    if phid is None:
        return None
    if cache.has(phid):
        return cache.get(phid)
    phab = Phabricator()
    data = phab.phid.lookup(names=[phid, ])
    name = data[phid]['name']
    cache.set(phid, name)
    return name


def phab_timestamp_to_date(timestamp):
    if timestamp is None:
        return None
    return datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')


def phab_url(phid):
    return '%s/%s' % (settings.PHAB_BASE_URL, phid)


def list_projects(query):
    phab = Phabricator()
    after, total_results = None, 0
    while True:
        results = phab.project.search(
            constraints=dict(
                query=query,
            ),
            after=after)
        for result in results.data:
            fields = result.get('fields', {})
            parent = fields.get('parent', {}) or {}
            slug = result.get('fields', {}).get('slug')
            phid = result.get('phid')
            name = slug or fields.get('name')
            url = '%s/project/profile/%s' % (settings.PHAB_BASE_URL, result.get('id'))
            print '%s\t%s\t%s' % (url, phid, slug or name)
        after = results['cursor']['after']
        if after is None:
            break


def query_project(project, column=None):
    cache.load()
    phab = Phabricator()
    constraints = {
        # 'statuses': ['open'],  # TODO: move to config
        'projects': [project],
        # createdStart
    }
    if column:
        constraints['columnPHIDs'] = [column, ]
    after = None
    while True:
        results = phab.maniphest.search(
            after=after,
            constraints=constraints,
            attachments={
                'columns': True,
                'subscribers': True,
                # 'projects': True,
            })
        for result in results.data:
            yield result
        cache.update()
        after = results['cursor']['after']
        if after is None:
            break


def get_task(phid):
    cache.load()
    phab = Phabricator()
    # don't use phab.maniphest.info(), different result format from
    # phab.maniphest.search -> keep them consistent
    results = phab.maniphest.search(
        constraints={
            'ids': [int(phid), ],
        },
        attachments={
            'columns': True,
            'subscribers': True,
            # 'projects': True,
        })
    for result in results.data:
        cache.update()
        return result
    raise KeyError('Could not find Phabricator task with ID %s' % phid)


def get_comments(phid):
    phab = Phabricator()
    transactions_set = phab.maniphest.gettasktransactions(ids=[phid, ])
    transactions = transactions_set[str(phid)]
    return [t for t in transactions if t.get('comments') is not None]


def add_backlink_comment(phid, jira_issue_key, jira_issue_url):
    phab = Phabricator()
    phab.maniphest.edit(
        objectIdentifier=phid,
        transactions=[dict(
            type='comment',
            value="""#Jira: %s
Migrated to JIRA: %s""" % (jira_issue_key, jira_issue_url),
        )])


def update_task_status(phid, status):
    phab = Phabricator()
    results = phab.maniphest.update(id=int(phid), status=status)


def update_task_column(phid, new_column_phid):
    phab = Phabricator()
    results = phab.maniphest.edit(
        objectIdentifier=phid,
        transactions=[
            {
                'type': 'column',
                'value': [new_column_phid, ],
            }
        ],
    )
