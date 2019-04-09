

python phab2jira.py

pip install ipython
jirashell -s https://jira.corp.dropbox.com --oauth-dance

Docs
https://github.com/disqus/python-phabricator
https://jira.readthedocs.io/en/master/
https://developer.atlassian.com/server/jira/platform/jira-rest-api-examples/

Steps
- Loop through all items in phab matching a query

Tools

- Command line to auth to JIRA and save credentials
  `phab2jira auth --server https://jira.corp.mycompany.com --username foo@bar.com --password foobar`
- Command line to list all phab projects
  `phab2jira projects --query myteam`
- Command line to test phab query
  `phab2jira query --project my_team_alias`
- Command line to create or update ONE issue in JIRA
  `phab2jira sync --phid T296627`
- Command line to create or update ALL issues in a phab query
  `phab2jira sync --project my_team_alias`

# Getting Started

## Install

```
virtualenv .virtualenv
source .virtualenv/bin/activate
pip install -r requirements.txt
```

## Authenticate to Phabricator

See: https://secure.phabricator.com/book/phabricator/article/arcanist_quick_start/

Run `arc install-certificate`

This should install a `~/.arcrc` file.

Test with `phab2jira list --project my_team_alias`.

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


# TODO

- Config for Phabricator URL prefix
- Config for mapping file
- Map task type again
- Add back URL for Phab issues and projects to console output
- Install as command-line tool
