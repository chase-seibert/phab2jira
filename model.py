import settings
import labels


def user_phid_to_email(user_phid):
    from lib_phab import phid_to_name
    if not user_phid:
        return None
    username = phid_to_name(user_phid)
    email = '%s%s' % (username, settings.EMAIL_DOMAIN_SUFFIX)
    return dict(name=email) if email else None


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
        from lib_phab import phab_url as _phab_url
        return _phab_url(self.phid)

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
        default = settings.JIRA_DEFAULT_STATUS
        value = self._fields['status']['value']
        return settings.PHAB_TO_JIRA_STATUS_MAP.get(value, default)

    @property
    def issuetype(self):
        source_field = settings.PHAB_ISSUE_TYPE_FIELD
        field_map = settings.PHAB_TO_JIRA_ISSUE_TYPE_MAP
        default = settings.PHAB_TO_JIRA_ISSUE_TYPE_DEFAULT
        if not source_field or not field_map:
            return default
        custom_type = self._fields[source_field]
        value = field_map.get(custom_type, default)
        return dict(name=value) if value else None

    @property
    def subscribers(self):
        attachments = self._obj.get('attachments', {})
        subscriber_phids = attachments.get('subscribers', {}).get('subscriberPHIDs', [])
        return [phid_to_name(phid) for phid in subscriber_phids]

    @property
    def story_points(self):
        points = self._fields['points']
        if points == '0.5':
            return 0.5
        return int(points) if points else None

    @property
    def priority(self):
        priority_name = self._fields['priority']['name']
        mapping = settings.PHAB_TO_JIRA_PRIORITY_MAP
        return dict(name=mapping.get(priority_name, priority_name))

    @property
    def description(self):
        # TODO: format?
        return Story.format_text(self._fields['description']['raw'])

    @property
    def assignee(self):
        return user_phid_to_email(self._fields['ownerPHID'])

    @property
    def reporter(self):
        return user_phid_to_email(self._fields['authorPHID'])

    @property
    def labels(self):
        from lib_phab import phid_to_name
        tags = set()
        attachments = self._obj.get('attachments', {})
        boards = attachments.get('columns', {}).get('boards', {})
        for project_phid, project in boards.items():
            board = project['columns'][0]
            tags.add(board['name'])
            project_name = phid_to_name(project_phid)
            tags.add(project_name)
        # list does not work, but tuple does?
        return labels.generate_labels(tags)

    @staticmethod
    def format_text(text):
        import re
        # very basic remarkup to wiki markdown conversion
        text = text.replace('**', '*')  # bold
        text = text.replace('~~', '-')  # deleted
        text = re.sub('//(.*?)//', r'_\1_', text)  # italics
        text = text.replace('```', '{code}')
        # links
        text = re.sub('\[(.*?)\]\((.*?)\)', r'[\1|\2]', text)
        # monospace
        text = re.sub('`(.*?)`', r'{{\1}}', text)
        # maniphest links & phabricator diff links
        text = re.sub('https\S+((T|D)[0-9]{4,})', r'\1' , text) # inside links
        text = re.sub('((T|D)[0-9]{4,})', r'[\1|%s/\1]' % settings.PHAB_BASE_URL, text)
        text = text.replace('[]', '[ ]')  # deleted
        return text

    @classmethod
    def get_comment_text(cls, comment_obj):
        from lib_phab import phab_timestamp_to_date
        return """Original comment by [~%s] on %s:

%s""" % (
            user_phid_to_email(comment_obj['authorPHID'])['name'],
            phab_timestamp_to_date(int(comment_obj['dateCreated'])),
            Story.format_text(comment_obj['comments']))

    def to_jira(self, fields=None):
        data = dict(
            summary=self.title,
            description=self.description,
            issuetype=self.issuetype,
            priority=self.priority,
            assignee=self.assignee,
            # reporter=self.reporter,
            labels=self.labels,
        )
        if settings.JIRA_STORY_POINTS_FIELD:
            data[settings.JIRA_STORY_POINTS_FIELD] = self.story_points
        for field, _callable in settings.FIELD_MAPS.items():
            value = _callable(self._obj)
            if value is not None:
                data[field] = _callable(self._obj)
        # post-processing, string None values
        data = {key: value for key, value in data.items() if value is not None}
        if fields:
            # only return a subset; useful for initial creation
            return {key: data[key] for key in fields}
        return data

    def __unicode__(self):
        return str(self)

    def __str__(self):
        return ('''=== %s ===
Title: %s''' % (self.phab_url, self.title)).encode('utf-8')
