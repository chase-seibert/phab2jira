# phab2jira - Migrate Phabricator Maniphest tasks to JIRA issues

Phabricator and JIRA both support CSV export/import. But you loose a lot of the
rich metadata for your issues, such as comments, links to the original tasks.
Plus, Phabricator Remarkup does not look good when displayed as JIRA Wiki
markup.

## What it does

- Migration one or all issues in a specific Phabricator project
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

### PHAB_BASE_URL

This is a convenience setting so that you don't have to specify the `--project`
argument all the time.

```python
PHAB_BASE_URL = 'my-project-alias'
```

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
