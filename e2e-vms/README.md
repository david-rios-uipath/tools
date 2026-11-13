# e2e-vms

Shows which staging VM each e2e-failure-investigator run is on right now, with its public IP, so you can RDP in and
tail `C:\vm-agent\notes\<run>\claude-<phase>.jsonl`.

```
$ e2e-vms
VM              ALIAS           IP          STATE    STARTED  PHASE        RUN                                    JOB
VM0000000000A1  investigator-0  192.0.2.10  Running  15:01    investigate  some-spec-20260101-120000-abcd         1a2b3c4d
VM0000000000B2  investigator-2  192.0.2.12  Running  15:09    fixVerify    other-spec-20260101-120001-ef01        5e6f7a8b
```

- Under the table it asks you to pick a VM (fzf, or a numbered list without it). Picking one:
  - copies a PowerShell block that follows that VM's latest run's newest Claude transcript (text and tool calls only)
  - opens RDP to the VM in Windows App, with clipboard sharing on. Paste the block into PowerShell there.
- VM login: `cp .env.example .env` and fill in `VM_USER` / `VM_PASSWORD` (gitignored). The username goes in the
  `.rdp` file; the password is copied to the clipboard for the login prompt, since `.rdp` files can't hold one on
  macOS. Enter in the terminal then swaps the clipboard to the tail command.
- `--all` adds recently finished jobs. `--list` prints the table only.
- Needs `uip` signed in to the `staging` profile: `uip login --profile staging`.
- `PHASE` is `probe` for jobs started by `probe-phase.sh`, which have no flow step.
- `IP` is the VM's public address, read from the cloud-robot pool. RDP only accepts the access IP set on the
  pool's Remote Desktop dialog (Orchestrator → Machines → the pool → a VM's ⋮ → Remote Desktop).
- Times are UTC.
