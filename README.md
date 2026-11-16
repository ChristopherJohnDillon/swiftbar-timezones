# SwiftBar Timezones — a SwiftBar plugin

**A [SwiftBar](https://github.com/swiftbar/SwiftBar) plugin** that keeps the time zones you work
across in the macOS menu bar, with a 24-hour side-by-side planner for finding a meeting slot.

> **Requires SwiftBar** (free, open source): `brew install --cask swiftbar` or download it from
> [github.com/swiftbar/SwiftBar](https://github.com/swiftbar/SwiftBar/releases).

**In the menu bar:** an emoji + the local time for each zone you pick, e.g. `🌴04:15 🗽07:15 🇬🇧12:15`.
A zone turns **orange** when it's outside work hours there.

**Click it for:**
- every zone you track (including ones you keep out of the menu bar), with its abbreviation
- a 24-hour table, one row per hour of your home zone's day, every zone side by side:
  **green "best"** when everyone is inside work hours, **amber "ok"** when everyone is inside
  stretch hours, and `◀ now` on the current hour
- **click any row to copy it**, e.g. `07:00 PST / 10:00 EST / 15:00 GMT`, ready to paste into an invite

Stdlib-only Python 3.9+, so it runs on the `python3` that ships with macOS. No network, no tokens.

## Install

1. **Install SwiftBar** and open it once so it asks for a plugin folder.
2. Run the setup wizard:

```sh
git clone https://github.com/ChristopherJohnDillon/swiftbar-timezones.git
cd swiftbar-timezones
python3 install.py
```

The wizard walks you through:

1. **Which zones**: pick from a numbered list of common cities, or type any city / IANA zone
   name (`Kolkata`, `Europe/Warsaw`, …). They're sorted west to east for you.
2. **An emoji for each zone**: Enter takes the suggestion (🗽 New York, 🇯🇵 Tokyo, …), or paste your
   own (Ctrl+Cmd+Space opens the emoji picker). Type `-` for no emoji, which shows `EST`-style text instead.
3. **Menu bar or dropdown only**: keep the menu bar to 3–4 zones; the rest still show when you click.
4. **Home zone**: the planner table runs midnight to midnight in this zone.
5. **Work and stretch hours** (default 9–17 and 8–18).

It previews the menu bar, saves `~/.config/swiftbar-timezones/config.json`, and copies the plugin
into your SwiftBar folder.

**To change zones later, re-run `python3 install.py`.** Your current answers are the defaults, so
you can just press Enter through the parts you're keeping. `--no-install` only rewrites the config.

## Config

You can also edit the config by hand:

```json
{
  "home": "Europe/London",
  "work": [9, 17],
  "stretch": [8, 18],
  "zones": [
    {"tz": "America/Los_Angeles", "emoji": "🌴", "menubar": true},
    {"tz": "America/Denver", "emoji": "🏔️", "menubar": false},
    {"tz": "America/New_York", "emoji": "🗽", "menubar": true},
    {"tz": "Europe/London", "emoji": "🇬🇧", "menubar": true}
  ]
}
```

If the file is broken, the plugin falls back to PT / ET / UK and says so in the dropdown.

## Notes

- Refreshes every second (`.1s.` in the filename); rename it to e.g. `timezones.10s.py` to refresh less often.
- SwiftBar's click actions break when the plugin path contains spaces (an iCloud Drive folder, for
  example), so the installer adds a space-free link at `~/.local/bin/tz-planner` in that case.
- The orange is a 256-colour ANSI code, because 24-bit colour codes render white in the menu bar.

## License

MIT
