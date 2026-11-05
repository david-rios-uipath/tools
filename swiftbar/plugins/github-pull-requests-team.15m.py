#!/usr/bin/env PYTHONIOENCODING=UTF-8 python3

# Requirements:
# - Python 3.x
# - ago (pip install ago)

import os
import sys
import datetime
import json
import time
import shutil
import subprocess
from ago import human

# Config lives at the repo root, one level up from this plugin
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

# Check if the .env file exists
if not os.path.exists(".env"):
    print("⚠ Github setup | color=red")
    print("---")
    print("⚠ .env file not found")
    sys.exit(0)

# Read the .env file
env_vars = {}
with open(".env", "r") as file:
    for line in file:
        if "=" in line:
            key, value = line.strip().split("=", 1)
            env_vars[key] = value


# (required) Auth token used against the GitHub GraphQL API.
# Prefers the GitHub CLI OAuth token (`gh auth login`), which works across an
# SSO-enforced org; falls back to GITHUB_ACCESS_TOKEN from .env.
def get_github_token():
    gh = shutil.which("gh") or "/opt/homebrew/bin/gh"
    try:
        token = subprocess.check_output(
            [gh, "auth", "token"], stderr=subprocess.DEVNULL, text=True
        ).strip()
        if token:
            return token
    except Exception:
        pass
    return env_vars.get("GITHUB_ACCESS_TOKEN")


GITHUB_ACCESS_TOKEN = get_github_token()

# (required) Your GitHub login https://github.com/<login>
GITHUB_LOGIN = env_vars.get("GITHUB_LOGIN")

# (required) GitHub org to search for open PRs
GITHUB_ORG = env_vars.get("GITHUB_ORG")

# (optional) Shows all PRs in draft also
SHOW_ALL_DRAFTS = True

# (optional) Non-draft PRs at least this many days old are flagged as stale
STALE_DAYS = 7

try:
    # For Python 3.x
    from urllib.request import Request, urlopen
except ImportError:
    # For Python 2.x
    from urllib2 import Request, urlopen


# Team members come from team-mapping.json at the repo root (gitignored, local only)
TEAM_MAPPING_PATH = "team-mapping.json"
if not os.path.exists(TEAM_MAPPING_PATH):
    print("⚠ Github setup | color=red")
    print("---")
    print("⚠ team-mapping.json not found, copy team-mapping.example.json")
    sys.exit(0)
with open(TEAM_MAPPING_PATH, "r") as mapping_file:
    team_mapping = json.load(mapping_file)

# (optional, local-only) team-mapping.local.json narrows the full mapping to
# just the people you want to watch. It is a *filter config*, not a member
# list -- member data stays in team-mapping.json. Shape:
#   {
#     "managers": ["manager@example.com"],  # include everyone reporting to these managers
#     "include":  ["some-github-login"]          # always-include these logins (whitelist)
#   }
# A login is shown if it's in `include` OR its `manager` is in `managers`.
# Whitelisted logins that aren't in team-mapping.json at all are still queried.
# If the file is absent, every member of team-mapping.json is shown (original behavior).
LOCAL_FILTER_PATH = "team-mapping.local.json"
if os.path.exists(LOCAL_FILTER_PATH):
    with open(LOCAL_FILTER_PATH, "r") as local_file:
        local_cfg = json.load(local_file)
    managers_filter = {m.strip().lower() for m in local_cfg.get("managers", [])}
    include_logins = [u.strip() for u in local_cfg.get("include", []) if u.strip()]

    # Whitelist first (preserves the order you list them, may include
    # people outside the mapping), then everyone under the chosen managers.
    users = list(dict.fromkeys(include_logins))
    for member in team_mapping:
        login = member.get("githubLogin")
        manager = (member.get("manager") or "").strip().lower()
        if login and manager in managers_filter and login not in users:
            users.append(login)
else:
    users = [member["githubLogin"] for member in team_mapping]

# Build the search query string
search_queries = [
    f"author:{user} is:pr is:open org:{GITHUB_ORG} archived:false" for user in users
]
search_query = " ".join(search_queries)

# GitHub caps the `search` connection at 100 records per page, so we fetch a
# page at a time and follow `pageInfo` cursors until every PR is collected.
def build_query(after=None):
    after_arg = ', after: "%s"' % after if after else ""
    return """
{
  search(query: "%s", type: ISSUE, first: 100%s) {
    pageInfo {
      hasNextPage
      endCursor
    }
    edges {
      node {
        ... on PullRequest {
          title
          url
          createdAt
          baseRefName
          headRefName
          author {
            login
          }
          reviews(first: 100, states: [APPROVED, CHANGES_REQUESTED]) {
            totalCount
            nodes {
              state
              author {
                login
              }
            }
          }
          comments {
            totalCount
          }
          labels(first:100) {
            nodes {
              name
            }
          }
          isDraft
          autoMergeRequest {
            enabledBy {
              login
            }
          }
        }
      }
    }
  }
}
""" % (
        search_query,
        after_arg,
    )

colors = {
    "inactive": "#8b949e",
    "title": None,
    "owner": "#2f81f7",
    "stale": "#db6d28",
}


def execute_query(query):
    headers = {
        "Authorization": "bearer " + GITHUB_ACCESS_TOKEN,
        "Content-Type": "application/json",
    }
    data = json.dumps({"query": query}).encode("utf-8")
    req = Request("https://api.github.com/graphql", data=data, headers=headers)
    body = urlopen(req).read()
    return json.loads(body)


def parse_date(text):
    utc = datetime.datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ")
    epoch = time.mktime(utc.timetuple())
    offset = datetime.datetime.fromtimestamp(
        epoch
    ) - datetime.datetime.utcfromtimestamp(epoch)
    return utc + offset


def print_line(text, **kwargs):
    print(build_line(text, **kwargs))


def build_line(text, **kwargs):
    text = text.replace("|", "-").replace("\n", " ")  # GitHub text must not inject xbar params
    kwargs = {k: v for k, v in kwargs.items() if v is not None}  # None = system default
    params = " ".join(["%s=%s" % (key, value) for key, value in kwargs.items()])
    return "%s | %s" % (text, params) if kwargs.items() else text


if not all([GITHUB_ACCESS_TOKEN, GITHUB_LOGIN, GITHUB_ORG]):
    print_line("⚠ Github setup", color="red")
    print_line("---")
    print_line("GITHUB_ACCESS_TOKEN, GITHUB_LOGIN and GITHUB_ORG cannot be empty")
    sys.exit(0)


nodes = []
after = None
while True:
    response = execute_query(build_query(after))
    search = response["data"]["search"]
    nodes.extend(search["edges"])
    page_info = search["pageInfo"]
    if not page_info["hasNextPage"]:
        break
    after = page_info["endCursor"]

def pr_age_days(pr):
    return (datetime.datetime.now() - parse_date(pr["createdAt"])).days


def build_pr_line(pr, author, is_draft, depth=0, prefix="", show_repo=True):
    title = pr["title"].replace("|", "-")
    comments_count = pr["comments"]["totalCount"]
    time_ago = human(parse_date(pr["createdAt"]))
    age_days = pr_age_days(pr)
    repo_name = pr["url"].split("/")[4]

    approved_count = sum(
        1 for review in pr["reviews"]["nodes"] if review["state"] == "APPROVED"
    )
    needs_work_count = sum(
        1
        for review in pr["reviews"]["nodes"]
        if review["state"] == "CHANGES_REQUESTED"
    )

    # Stale only applies to review-ready (non-draft) PRs sitting open too long
    is_stale = not is_draft and age_days >= STALE_DAYS

    counts = ""
    if approved_count > 0:
        counts += "% s ✅" % approved_count
    if comments_count > 0:
        counts += "%s 💬" % comments_count
    if needs_work_count > 0:
        counts += " %s ⛔️" % needs_work_count

    text = "[%s] - %s -- %s -- %s%s%s%s" % (
        author,
        "%s - %s" % (repo_name, title) if show_repo else title,
        counts,
        time_ago,
        " 🚧 DRAFT 🚧" if is_draft else "",
        " 🦾 Auto-merge" if pr["autoMergeRequest"] else "",
        " 🕰️ %sd stale" % age_days if is_stale else "",
    )

    if author == GITHUB_LOGIN:
        color = colors["owner"]
    elif is_draft:
        color = colors["inactive"]
    elif is_stale:
        color = colors["stale"]
    else:
        color = colors["title"]

    # xbar nests an item under the previous line by prefixing it with "--"
    return build_line("--" * depth + prefix + text, size=12, color=color, href=pr["url"])


def repo_of(pr):
    return pr["url"].split("/")[4]


def group_stacks(prs):
    """Split newest-first PRs into units: a lone PR, or a stack listed bottom-to-top.

    A PR is stacked when its base branch is another open PR's head branch in the same repo.
    """
    by_head = {(repo_of(pr), pr["headRefName"]): pr for pr in prs}
    parent = lambda pr: by_head.get((repo_of(pr), pr["baseRefName"]))
    kids = {}
    for pr in prs:
        if parent(pr):
            kids.setdefault(parent(pr)["url"], []).append(pr)

    def walk(pr):
        out = [pr]
        for kid in reversed(kids.get(pr["url"], [])):  # oldest kid first
            out.extend(walk(kid))
        return out

    units, done = [], set()
    for pr in prs:  # a stack sits where its newest PR would
        if pr["url"] in done:
            continue
        root = pr
        while parent(root):
            root = parent(root)
        unit = walk(root)
        done.update(m["url"] for m in unit)
        units.append(unit)
    return units


def unit_lines(unit, author, depth):
    if len(unit) == 1:
        return [build_pr_line(unit[0], author, unit[0]["isDraft"], depth)]
    root = unit[0]
    label = "📚 %s - %s (%d PRs) → %s" % (
        repo_of(root), root["headRefName"], len(unit), root["baseRefName"]
    )
    # Merging the tip lands everything below it, so the tip's auto-merge covers the stack
    if unit[-1]["autoMergeRequest"]:
        label += " 🦾 Auto-merge"
    out = [build_line(
        "--" * depth + label,
        size=12,
        color=colors["owner"] if author == GITHUB_LOGIN else None,
    )]
    # Rendered bottom-to-top: tip of the stack first, base PR last
    out.extend(
        build_pr_line(pr, author, pr["isDraft"], depth + 1, "%d/%d " % (i, len(unit)), show_repo=False)
        for i, pr in reversed(list(enumerate(unit, 1)))
    )
    return out


pr_count = 0
lines = []

# Group every PR (drafts included) by author
prs_by_user = {}
for edge in nodes:
    pr = edge["node"]
    author = pr["author"]["login"]
    if pr["isDraft"] and author != GITHUB_LOGIN and not SHOW_ALL_DRAFTS:
        continue
    prs_by_user.setdefault(author, []).append(pr)

for prs in prs_by_user.values():
    prs.sort(key=lambda pr: parse_date(pr["createdAt"]), reverse=True)

# You first, then whoever opened the newest PR
sorted_authors = sorted(
    prs_by_user,
    key=lambda a: (a == GITHUB_LOGIN, prs_by_user[a][0]["createdAt"]),
    reverse=True,
)

for author in sorted_authors:
    prs = prs_by_user[author]
    pr_count += len(prs)

    # A unit (lone PR or stack) counts as draft only if every PR in it is a draft
    units = group_stacks(prs)
    ready = [u for u in units if not all(pr["isDraft"] for pr in u)]
    drafts = [u for u in units if all(pr["isDraft"] for pr in u)]

    if author == GITHUB_LOGIN:
        # Drafts last, no divider
        for unit in ready + drafts:
            lines.extend(unit_lines(unit, author, depth=0))
        lines.append("---")
        continue

    # Everyone else: a submenu with ready PRs, a divider, then drafts
    ready_count = sum(not pr["isDraft"] for pr in prs)
    label = "%s (%s)" % (author, ready_count)
    if ready_count < len(prs):
        label += " · %s 🚧" % (len(prs) - ready_count)
    lines.append(build_line(label))
    for unit in ready:
        lines.extend(unit_lines(unit, author, depth=1))
    if ready and drafts:
        lines.append("-----")
    for unit in drafts:
        lines.extend(unit_lines(unit, author, depth=1))


print("%s 🧑‍💻" % pr_count)
print("---")
for line in lines:
    print(line)
