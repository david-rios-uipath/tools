# e2e-vms

Shows which staging VM each e2e-failure-investigator run is on right now, so you can RDP in and
tail `C:\vm-agent\notes\<run>\claude-<phase>.jsonl`.

```
$ e2e-vms
VM              STATE    STARTED  PHASE        RUN                                    JOB
VM0000000000A1  Running  15:01    investigate  some-spec-20260101-120000-abcd         1a2b3c4d
VM0000000000B2  Running  15:09    fixVerify    other-spec-20260101-120001-ef01        5e6f7a8b
```

- `--all` adds recently finished jobs.
- Needs `uip` signed in to the `staging` profile: `uip login --profile staging`.
- `PHASE` is `probe` for jobs started by `probe-phase.sh`, which have no flow step.
- Times are UTC.
