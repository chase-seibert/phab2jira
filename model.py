import settings


class Story(object):

    def __init__(self, phid, title, description, date_created,
                 status, priority, points, task_type, assigned, tags, author, subsribers):
        self.phid = phid
        self.title = title
        self.description = description
        self.date_created = date_created
        self.status = status
        self.priority = priority
        self.points = points
        self.task_type = task_type
        self.assigned = assigned
        self.tags = tags
        self.author = author
        self.subsribers = subsribers
        self.phab_base_url = settings.PHAB_BASE_URL

    @classmethod
    def from_phab(cls, obj):
        from lib_phab import phid_to_name, phab_timestamp_to_date
        fields = obj['fields'] or {}
        tags = []
        attachments = obj.get('attachments', {})
        boards = attachments.get('columns', {}).get('boards', {})
        for project_phid, project in boards.items():
            board = project['columns'][0]
            project_name = phid_to_name(project_phid)
            tags.append('%s:%s' % (project_name, board['name']))
        subscriber_phids = attachments.get('subscribers', {}).get('subscriberPHIDs', [])
        subsribers = [phid_to_name(phid) for phid in subscriber_phids]
        # import pdb; pdb.set_trace()
        # import ipdb; ipdb.set_trace()
        return cls(
            phid='T%s' % obj['id'],
            title=fields['name'],
            description=fields['description'],  # TODO: format?
            date_created=phab_timestamp_to_date(fields['dateCreated']),  # TODO: parse '1501274237'
            status=fields['status']['value'],  # TODO: map to JIRA?
            priority=fields['priority']['value'],  # TODO: int to enum?
            points=fields['points'],
            task_type=None,
            assigned=phid_to_name(fields['ownerPHID']),  # TODO: translate to username
            tags=tags,
            author=phid_to_name(fields['authorPHID']),
            subsribers=subsribers,
            # TODO: comments
            # TODO: images
        )

    def __unicode__(self):
        return str(self)

    def __str__(self):
        return ('''=== %(phab_base_url)s/%(phid)s ===
ID: %(phid)s
Title: %(title)s
Author: %(author)s
Date: %(date_created)s
Priority: %(priority)s
Status: %(status)s
Points: %(points)s
Type: %(task_type)s
Assigned: %(assigned)s
Subscribers: %(subsribers)s
Tags: %(tags)s''' % self.__dict__).encode('utf-8')
