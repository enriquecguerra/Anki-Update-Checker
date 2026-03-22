# Update Checker

Update Checker compares your installed Anki Desktop version with the latest official stable release.

AnkiWeb page: https://ankiweb.net/shared/info/323305297

## Highlights

- Tools submenu: `Tools -> Update Checker`
- Manual action: `Check for Updates`
- Settings action: `Change Configuration`
- Startup checks with configurable interval
- Native `Upgrade/Downgrade` prompt when available
- Official download page fallback when native upgrade path is unavailable

## Compatibility

- Anki Desktop `24.04+`
- Python `3.9+`
- Windows, macOS, Linux

## Usage

1. Install the add-on.
2. Restart Anki.
3. Open `Tools -> Update Checker`.
4. Use `Check for Updates` to run an immediate check.
5. Use `Change Configuration` to update behavior.

## Configuration UI

The `Change Configuration` dialog lets you set:

- `Automatic checks` on profile open
- `Check interval`:
- `Startup` (default)
- `Every day`
- `Every 7 days`
- `Every 30 days`
- `Custom...` (`5m`, `5h`, `5d`, `startup`, `never`, or numeric days like `2`)
- `Download page URL`

## Runtime Behavior

- Startup check errors are silent.
- Manual check errors are shown.
- Manual checks show an explicit “up to date” message when no update is found.
- Only stable releases are considered.

## Config File

Default config:

```json
{
  "check_on_startup": true,
  "check_interval": "startup",
  "download_page_url": "https://apps.ankiweb.net/",
  "_last_check_ts": 0,
  "_last_known_latest": ""
}
```

Detailed key reference: [config.md](./addon/config.md)  
Developer docs: [DEVELOPMENT.md](./addon/DEVELOPMENT.md)

## Repository Notes

- Add-on source lives in [`addon/`](./addon).
- Unit tests live in [`tests/`](./tests).
- The repository does not track built release archives (`*.ankiaddon`).
- Build `.ankiaddon` from the contents of `addon/`, then publish via GitHub Releases or AnkiWeb.
