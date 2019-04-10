import settings


class Story(object):

    def __init__(self, obj):
        self._obj = obj
        self._fields = obj['fields'] or {}

    @classmethod
    def from_phab(cls, obj):
        return cls(obj)

    @property
    def phid(self):
        return 'T%s' % self._obj['id']

    @property
    def phab_base_url(self):
        return settings.PHAB_BASE_URL

    @property
    def phab_url(self):
        return '%s/%s' % (settings.PHAB_BASE_URL, self.phid)

    @property
    def phab_title(self):
        return '%s: %s' % (self.phid, self._fields['name'])

    @property
    def title(self):
        return self._fields['name'][:255]

    @property
    def tags(self):
        from lib_phab import phid_to_name
        tags = []
        attachments = self._obj.get('attachments', {})
        boards = attachments.get('columns', {}).get('boards', {})
        for project_phid, project in boards.items():
            board = project['columns'][0]
            project_name = phid_to_name(project_phid)
            tags.append('%s:%s' % (project_name, board['name']))
        return tags

    @property
    def status(self):
        return self._fields['status']['value']

    @property
    def subscribers(self):
        attachments = self._obj.get('attachments', {})
        subscriber_phids = attachments.get('subscribers', {}).get('subscriberPHIDs', [])
        return [phid_to_name(phid) for phid in subscriber_phids]

    @property
    def story_points(self):
        points = self._fields['points']
        return int(points) if points else None

    @property
    def priority(self):
        priority_name = self._fields['priority']['name']
        mapping = settings.PHAB_TO_JIRA_PRIORITY_MAP
        return dict(name=mapping.get(priority_name, priority_name))

    @property
    def description(self):
        # TODO: format?
        return self._fields['description']['raw']

    def to_jira(self, fields=None):
        data = dict(
            summary=self.title,
            description=self.description,
            issuetype=None,  # must be set by a callable, can't auto map
            priority=self.priority,
        )
        if settings.JIRA_STORY_POINTS_FIELD:
            data[settings.JIRA_STORY_POINTS_FIELD] = self.story_points
        for field, _callable in settings.FIELD_MAPS.items():
            value = _callable(self._obj)
            if value is not None:
                data[field] = _callable(self._obj)
        if fields:
            # only return a subset; useful for initial creation
            return {key: data[key] for key in fields}
        return data

    def __unicode__(self):
        return str(self)

    def __str__(self):
        return ('''=== %s ===
Title: %s''' % (self.phab_url, self.title)).encode('utf-8')
