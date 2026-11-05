# SwiftBar plugins

macOS menu bar plugins. Config lives in this folder; the plugins themselves are in `plugins/`.

## SwiftBar, not xbar

These plugins are meant to run on [SwiftBar](https://github.com/swiftbar/SwiftBar), not xbar. That choice is deliberate, for reliability. The output format is xbar-compatible, but only SwiftBar is tested.

## Setup

1. Install SwiftBar:

   ```sh
   brew install --cask swiftbar
   ```

2. In SwiftBar, set the plugin folder to this repo's `swiftbar/plugins/` directory.

3. Copy the example config for each plugin you use (see below).

The number in a plugin's file name sets its refresh interval (`15m` = every 15 minutes).

## Plugins

### `github-pull-requests-team.15m.py`

Lists your team's open pull requests in one GitHub org.

- You first, then teammates by most recent PR
- Ready PRs, then drafts, per person
- Stacked PRs grouped under a 📚 header, tip at the top, base at the bottom
- 🦾 Auto-merge on a stack header when the tip PR has auto-merge on
- Approvals ✅, comments 💬, changes requested ⛔️, stale PRs 🕰️

#### Setup

Run from this `swiftbar/` folder:

```sh
pip3 install ago
gh auth login   # the plugin uses the GitHub CLI token
cp .env.example .env
cp team-mapping.example.json team-mapping.json
```

Edit `.env` (`GITHUB_LOGIN`, `GITHUB_ORG`) and `team-mapping.json` (one entry per teammate).

#### Team details stay local

`.env`, `team-mapping.json` and `team-mapping.local.json` are gitignored. Teammates' names, emails and reporting lines never go into the repo. Only the `*.example*` files are committed.

#### Optional filter

`team-mapping.local.json` narrows the list without editing the mapping (see `team-mapping.local.example.json`):

- `managers`: show everyone whose `manager` is in this list
- `include`: always show these logins, even ones not in the mapping

Without the file, everyone in `team-mapping.json` is shown.
