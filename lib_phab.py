from datetime import datetime

from phabricator import Phabricator

import cache

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
            print '%s %s' % (phid, slug or name)
        after = results['cursor']['after']
        if after is None:
            break


def query_project(project):
    cache.load()
    phab = Phabricator()
    after = None
    while True:
        results = phab.maniphest.search(
            after=after,
            constraints={
                'statuses': ['open'],  # TODO: move to config
                'projects': [project],
            },
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
