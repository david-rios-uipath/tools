# swiftbar-github-team-prs

A macOS menu bar plugin listing your team's open pull requests in one GitHub org.

- You first, then teammates by most recent PR
- Ready PRs, then drafts, per person
- Stacked PRs grouped under a 📚 header, tip at the top, base at the bottom
- 🦾 Auto-merge on a stack header when the tip PR has auto-merge on
- Approvals ✅, comments 💬, changes requested ⛔️, stale PRs 🕰️

## SwiftBar, not xbar

This plugin is meant to run on [SwiftBar](https://github.com/swiftbar/SwiftBar), not xbar. That choice is deliberate, for reliability. The plugin output format is xbar-compatible, but only SwiftBar is tested.

## Setup

1. Install SwiftBar and the Python dependency:

   ```sh
   brew install --cask swiftbar
   pip3 install ago
   ```

2. Log in with the GitHub CLI. The plugin uses its token:

   ```sh
   gh auth login
   ```

3. Create your local config from the examples:

   ```sh
   cp .env.example .env
   cp team-mapping.example.json team-mapping.json
   ```

   Edit `.env` (`GITHUB_LOGIN`, `GITHUB_ORG`) and `team-mapping.json` (one entry per teammate).

4. In SwiftBar, set the plugin folder to this repo's `plugins/` directory.

The `15m` in the file name sets the refresh interval to 15 minutes.

## Team details stay local

`.env`, `team-mapping.json` and `team-mapping.local.json` are gitignored. Teammates' names, emails and reporting lines never go into the repo. Only the `*.example*` files are committed.

### Optional filter

`team-mapping.local.json` narrows the list without editing the mapping (see `team-mapping.local.example.json`):

- `managers`: show everyone whose `manager` is in this list
- `include`: always show these logins, even ones not in the mapping

Without the file, everyone in `team-mapping.json` is shown.
