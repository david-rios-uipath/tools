# e2e-vms

Shows which staging VM each e2e-failure-investigator run is on right now, with its public IP, so you can RDP in and
tail `C:\vm-agent\notes\<run>\claude-<phase>.jsonl`.

```
$ e2e-vms
VM              ALIAS           IP          STATE    STARTED  PHASE        RUN                                    JOB
VM0000000000A1  investigator-0  192.0.2.10  Running  15:01    investigate  some-spec-20260101-120000-abcd         1a2b3c4d
VM0000000000B2  investigator-2  192.0.2.12  Running  15:09    fixVerify    other-spec-20260101-120001-ef01        5e6f7a8b
```

- Under the table it prints a PowerShell block per VM that follows that run's newest Claude
  transcript (text and tool calls only). Paste it in the VM after RDP.
- `--all` adds recently finished jobs.
- Needs `uip` signed in to the `staging` profile: `uip login --profile staging`.
- `PHASE` is `probe` for jobs started by `probe-phase.sh`, which have no flow step.
- `IP` is the VM's public address, read from the cloud-robot pool. RDP only accepts the access IP set on the
  pool's Remote Desktop dialog (Orchestrator → Machines → the pool → a VM's ⋮ → Remote Desktop).
- Times are UTC.
