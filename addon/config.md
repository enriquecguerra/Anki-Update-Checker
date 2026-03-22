# Configuration Reference

## `check_on_startup` (boolean)

- `true`: allow automatic checks on profile open.
- `false`: disable automatic checks (manual checks still work).

## `check_interval` (string or number)

Primary interval control.

Supported values:

- `"startup"`, `"always"`, `"0"`, `"0s"`, `"0m"`, `"0h"`, `"0d"`: check every profile open.
- `"never"`, `"off"`, `"disabled"`: disable automatic checks.
- `"<N>s"`, `"<N>m"`, `"<N>h"`, `"<N>d"`: run every N seconds/minutes/hours/days.
- Number value: interpreted as days (legacy-friendly behavior).

If invalid, fallback is `startup` behavior.

## `download_page_url` (string)

Official download page opened by fallback/manual website path.

Default: `https://apps.ankiweb.net/`

## `_last_check_ts` (integer, internal)

Unix timestamp of last successful release fetch.

Used to enforce interval scheduling.

## `_last_known_latest` (string, internal)

Last upstream version tag observed by the add-on.

For diagnostic display/state only.

## Notes

- `check_interval_days` has been removed and is no longer used.
- `include_prereleases` has been removed and is no longer used.
- You can edit settings in-app via `Tools -> Update Checker -> Change Configuration`.
