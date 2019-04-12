# phab2jira - Bulk Migrate Phabricator Projects to JIRA

Phabricator and JIRA both support CSV export/import. But you loose a lot of the
rich metadata for your issues, such as comments, links to the original tasks.
Plus, Phabricator Remarkup does not look good when displayed as JIRA Wiki
markup.

## What it does

- Migrate one or all issues in a specific Phabricator project
- Filter out issues with specific Phabricator boards or statuses
- Map custom JIRA fields by writing Python code snippets to do the transform
- Custom issue type mapping
- Custom issue priority mapping
- Custom issue status mapping
- Doesn't need any special JIRA admin access; use your normal account

## Quickstart

```bash
virtualenv .virtualenv
source .virtualenv/bin/activate
pip install -r requirements.txt
python phab2jira.py --help
```

### Authenticate to Phabricator

Phabricator authentication should be automatic via your `~/.arcrc` credentials.
You can test it out by searching for Phabricator projects that match a certain
query string:

```bash
python phab2jira.py projects --query my-search-term
```

### Query for the Phabricator project/issues that you want to migrate

By using `python phab2jira.py projects`, you will get a list of Phabricator
projects by URL, ID and alias. Once you think you've found the right one, try
querying for all the tasks under a specific project alias, to check.

```bash
python phab2jira.py query --project my-project-alias
```

### Authenticate to JIRA

Even if you use single sign on to authenticate to JIRA normally, you also have
a regular username and password. You can set it by going to
`Profile -> Change Password`. Once you have your password, you can authenticate
on the command-line.

```bash
>python phab2jira.py auth --server https://my-jira-host --username my-username@my-domain.com --password my-password
Successfully connected to: https://my-jira-host
Version: 7.8.0
Connected as: Your Name
Wrote credentials to ~/.jirarc
```

If successful, the credentials will be cached in `~/.jirarc` so that you don't
need to provide them again.

### Migrate specific tasks as a test

Start by migrating tasks one-off, to test the migration and the mapping.

```bash
>python phab2jira.py sync --phid T261182 --jira-project my-jira-project-alias
=== https://my-phabricator-host/T261182 ===
Title: The title of by Phabricator task
...
Created: https://my-jira-host/browse/PROJ-1
```

Along with the links to the JIRA issues, the command will print a diff of what
fields it's setting on the JIRA issue.

*Note: the sync commands are idempotent; if you sync the same issue twice, it
uses create or update semantics to update the existing JIRA issue. The issue
tracking is done via a remote link that's created on the JIRA issues back to
exactly one Phabricator task.*

### Tweak the migration mapping

There are a number of settings you can tweak on the migration. See "Settings".

### Migrate everything

Once you're happy with your settings, you can migrate everything.

```bash
python phab2jira.py sync-all --project my-project-alias --jira-project my-jira-project-alias
```

It will page though all results; there is no limit. If you want to artificially
step through pages of results, you can use the optional `--limit` and `--offset`
arguments.


## Settings

You can create a `settings_override.py` file, and populate the following
settings:

### EMAIL_DOMAIN_SUFFIX

The email domain for your company. It's used to format email addresses from
usernames, when inserting references to specific users for task assignment and
comments attribution.

```python
EMAIL_DOMAIN_SUFFIX = '@domain.com'
```

### PHAB_BASE_URL

This setting is used to create the URLs for Phabricator tasks, both for console
output and more importantly for the back-links from JIRA to Phabricator.

```python
PHAB_BASE_URL = 'https://secure.phabricator.com'
```
### PHAB_DEFAULT_PROJECT

This is a convenience setting so that you don't have to specify the `--project`
argument all the time.

```python
PHAB_DEFAULT_PROJECT = 'my-project-alias'
```

### PHAB_ISSUE_TYPE_FIELD

If you have a custom field in Phabricator that tracks the type of Phabricator
issue, you can specify it here. See also `PHAB_TO_JIRA_ISSUE_TYPE_DEFAULT` and
`PHAB_TO_JIRA_ISSUE_TYPE_MAP`.

```python
PHAB_ISSUE_TYPE_FIELD = 'custom:my-field'
```

### PHAB_TO_JIRA_ISSUE_TYPE_DEFAULT

The default JIRA issue type you want to create, if there is no mapping.

```python
PHAB_TO_JIRA_ISSUE_TYPE_DEFAULT = 'Task'  # or Story, Bug
```

### PHAB_TO_JIRA_ISSUE_TYPE_MAP

The mapping for Phabricator task type to JIRA issue type.

```python
PHAB_TO_JIRA_ISSUE_TYPE_MAP = {
    'custom:feature': 'Story',
    'custom:bug': 'Bug',
}
```

### PHAB_TO_JIRA_STATUS_MAP

Map Phabricator task status to JIRA issue status.

```python
PHAB_TO_JIRA_STATUS_MAP = {
    'Open': 'open',
    'Resolved': 'done',
    'Needs Investigation': 'on hold',
    'In progress': 'in progress',
    'Verify Fix': 'in review',
}
```

### JIRA_DEFAULT_STATUS

The default issue status to use if there is no status mapping.

```python
JIRA_DEFAULT_STATUS = 'Open'
```

### JIRA_BASE_URL, JIRA_USERNAME, JIRA_PASSWORD

The URL of your JIRA instance. This can be used instead of using `phab2jira auth`
and creating a `~/.jirarc` file.

```python
JIRA_BASE_URL = 'https://my-jira-host'
JIRA_USERNAME = 'my-username@my-domain.com'
JIRA_PASSWORD = 'my-password'
```

### JIRA_DEFAULT_PROJECT

The project you want to import issues to be default, convenience so that you
don't have to pass `--jira-project`.

```python
JIRA_DEFAULT_PROJECT = 'my-jira-project-alias'  # ex: PROJ (whatever the prefix of your issues is, like PROJ-1)
```

### JIRA_STORY_POINTS_FIELD

If you have a custom field in JIRA for story points, you can specify it here.

```python
JIRA_STORY_POINTS_FIELD = 'customfield_10006'
```

### NO_MIGRATE_ISSUES_WITH_LABELS

Issues created in JIRA will have automatic labels created for them based on the
Phabricator work board and work board status. This can be useful for filtering
later. This setting lets you NOT create a set of issues because they have one of a
subset of labels.

```python
NO_MIGRATE_ISSUES_WITH_LABELS = [
  'my-label1',
  'my-label2',
]
```

### BLACKLISTED_USERS

JIRA will error out of you try to create a reference to a user that exists in
Phabricator, but not in JIRA. You can blacklist these users, and it will just
use email address instead of a real linked reference.

```python
BLACKLISTED_USERS = [
  'email1@domain.com',
  'email2@domain.com',
]
```

### ISSUES_TO_SKIP

If you encounter a small set of issues that cannot be migrated for any reason,
you can blacklist them by ID so that they will not attempt to migrate in the
future.

```python
ISSUES_TO_SKIP = [
  'T131970',
]
```

### FIELD_MAPS

This is a powerful extension mechanism that lets you write custom Python code
for certain field mappings. You use the map to specify a JIRA issue field name
and a callable function which created the value for that JIRA field based on the
Phabricator JSON object.

```python
def get_story_points(obj):
  points = obj['fields']['points']
  if not points:
      return None
  return int(points)


FIELD_MAPS = {
  'customfield_10006': get_story_points,
}
```

## Features

### Labels

The names of Phabricator work-boards/milestones are slugified and migrated to
JIRA labels. This means that if a Phabricator task was on work-board
`My Workboard`, it would have the label `my-workboard`. This makes it relatively
 easy to query in JIRA, and potentially batch edit to move under some JIRA
 Epic, or make other edits.

Phabricator tasks can be under multiple work-boards and milestones, which results
in a set of labels.

### Linking Phabricator task and diff references

Naked references to Phabricator tasks `T123456` and diffs `D123456`, which
are rendered natively as links in Phabricator, are converted to `[|]` link syntax.

### Remarkup to JIRA Wiki Markup

Basic best-effort attempts are made to migrate the Phabricator task and comment
body formatting from
[Remarkup](https://secure.phabricator.com/book/phabricator/article/remarkup/)
to [JIRA Wiki Markup](https://confluence.atlassian.com/doc/confluence-wiki-markup-251003035.html).

- Bold text migrated from `**` to `*` syntax.
- Strike-through text migrated from `~~` to `-` syntax.
- Code blocks migrated from triple back-ticks to `{code}` blocks.
- Links migrated from `[]()` syntax to `[|]` syntax.
- Monospace single back-ticks syntax migrated to `{{}}` syntax.
- Image `{img }` syntax migrated to `!!` syntax.

## Known issues

- The create date on the JIRA issues will be the current date; there is no way
to set this via the REST API.
- The issues reporter will be the user you are using to authenticate to JIRA.
Setting that is possible in the REST API, but it requires special admin permissions.
- The commenting user on any comments will be the user you are using to
authenticate to JIRA.
- The date of any comments will be now. BUT - the comment body will include the
original commenting user and date.


## Trouble-shooting

### Authenticating to Phabricator

See: https://secure.phabricator.com/book/phabricator/article/arcanist_quick_start/

Run `arc install-certificate`

This should install a `~/.arcrc` file.

## Authenticate to JIRA

Note: depending on your JIRA config, if you provide the wrong password to your
account even once, you may get the following CAPTCHA exception:

```
text: CAPTCHA_CHALLENGE; login-url=https://jira.corp.mycompany.com/login.jsp
...
response text = {"errorMessages":["Login denied"],"errors":{}}
```

In that case, if you simply open a browser and login to JIRA successfully, the
CAPTCHA will be cleared and you can try again from the command line.
