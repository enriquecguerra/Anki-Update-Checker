# Development Guide

## Architecture

The add-on is split into focused modules:

- `__init__.py`: thin entrypoint that registers hooks.
- `bootstrap.py`: hook wiring and runtime controller singleton.
- `controller.py`: orchestration of config, release lookup, scheduling, and user flows.
- `config_state.py`: config defaults, normalization, and persistence.
- `intervals.py`: interval parsing and scheduling checks.
- `release_client.py`: GitHub API access and release selection.
- `versioning.py`: version token parsing/comparison.
- `launcher_adapter.py`: native launcher detection/invocation and version source lookup.
- `ui.py`: menu wiring and UI/browser fallback helpers.
- `models.py`: typed runtime models and statuses.

## Runtime Flow

1. `profile_did_open` fires.
2. Add-on ensures `Tools -> Update Checker` submenu exists once.
3. Controller evaluates auto-check gating (`check_on_startup` + interval).
4. If due/manual, controller runs background fetch.
5. Controller computes result state (`update_available`, `up_to_date`, `error`).
6. Controller applies startup/manual messaging rules and update action prompts.

## Design Guarantees

- Unknown config keys are preserved when writing internal state, except deprecated keys explicitly removed by migration.
- `_last_check_ts` and `_last_known_latest` update only after successful release parse.
- Startup errors are silent; manual errors are visible.
- Stable update path prefers native launcher only when prerequisites are truly available.
- Fallback to official download page is always available.

## Testing

Run from project root:

```bash
python3 -m unittest discover -s tests -v
```

Test coverage includes:

- Interval parsing and scheduling decisions.
- Version parsing/comparison.
- Release selection/fallback behavior.
- Native launcher availability/invocation behavior.
- Controller startup/manual behavior.
- UI helper behavior for menu insertion, duplicate prevention, and URL fallback.
