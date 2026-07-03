# linkcheck

Link health (plan §6.3): ICAI reshuffles URLs often, and dead official links
destroy trust fastest.

- `.github/workflows/link-check.yml` — weekly sweep (Mondays 08:00 IST) of
  every URL in `src/data/`; on any 404/redirect failure it opens a
  `link-health` issue; on a fully green sweep it runs the updater below and
  commits the refreshed dates.
- `update_last_checked.py` — stamps every `lastChecked` (JS/JSON) and
  `last_checked` (YAML, incl. root `sources.yaml`) date. Question banks are
  excluded: their `lastVerified` means "content verified", which no link
  sweep may touch.

```sh
python3 scripts/linkcheck/update_last_checked.py            # stamp today
python3 scripts/linkcheck/update_last_checked.py --date '5 Jul 2026'
```
