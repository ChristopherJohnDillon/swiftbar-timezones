#!/usr/bin/env python3
# <xbar.title>Timezones Display</xbar.title>
# <xbar.version>v3.0</xbar.version>
# <xbar.author>Chris Dillon</xbar.author>
# <xbar.author.github>christopherjohndillon</xbar.author.github>
# <xbar.desc>Your time zones in the menu bar (orange = out of hours). Dropdown: every zone plus a 24-hour side-by-side table for planning meetings; click a row to copy it. Run install.py to pick zones and emojis.</xbar.desc>
# <xbar.dependencies>python</xbar.dependencies>
# <swiftbar.hideAbout>true</swiftbar.hideAbout>
# <swiftbar.hideRunInTerminal>true</swiftbar.hideRunInTerminal>
# <swiftbar.hideLastUpdated>true</swiftbar.hideLastUpdated>
# <swiftbar.hideDisablePlugin>true</swiftbar.hideDisablePlugin>
# <swiftbar.hideSwiftBar>true</swiftbar.hideSwiftBar>
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

CONFIG = os.path.expanduser("~/.config/swiftbar-timezones/config.json")
# Used until install.py writes a config — west to east
DEFAULT = {
    "home": "Europe/London",
    "work": [9, 17],
    "stretch": [8, 18],
    "zones": [
        {"tz": "America/Los_Angeles", "emoji": "🌴", "menubar": True},
        {"tz": "America/New_York", "emoji": "🗽", "menubar": True},
        {"tz": "Europe/London", "emoji": "🇬🇧", "menubar": True},
    ],
}
WHITE = "\033[0m"
ORANGE = "\033[38;5;209m"   # 256-colour works on the menu bar; 24-bit renders white
RESET = "\033[0m"
MONO = "font=Menlo size=13 trim=false"
GAP = "   "
# SwiftBar click actions break on paths with spaces (e.g. iCloud's "Mobile Documents"); install.py makes a space-free link
LINK = os.path.expanduser("~/.local/bin/tz-planner")
SELF = LINK if os.path.exists(LINK) else os.path.abspath(__file__)


def parse(cfg):
    zones = [(z.get("emoji", ""), ZoneInfo(z["tz"]), z.get("menubar", True)) for z in cfg["zones"]]
    if not zones:
        raise ValueError("no zones listed")
    home = ZoneInfo(cfg.get("home") or cfg["zones"][0]["tz"])
    return zones, home, tuple(cfg.get("work", (9, 17))), tuple(cfg.get("stretch", (8, 18)))


def load_config():
    """Return (zones, home, work, stretch, error); zones = [(emoji, ZoneInfo, in_menubar)]."""
    try:
        with open(CONFIG) as f:
            return parse(json.load(f)) + (None,)
    except FileNotFoundError:
        return parse(DEFAULT) + (None,)
    except Exception as e:  # bad JSON / unknown zone: fall back, but say so in the dropdown
        return parse(DEFAULT) + (f"{CONFIG}: {e}",)


ZONES, HOME, WORK, STRETCH, CONFIG_ERROR = load_config()


def in_hours(dt, rng):
    return rng[0] <= dt.hour < rng[1]


def slot_text(utc):
    return " / ".join(f"{utc.astimezone(tz).strftime('%H:%M')} {utc.astimezone(tz).tzname()}" for _, tz, _ in ZONES)


def copy_action(utc):
    return f'bash={SELF} param1=copy param2={utc.strftime("%Y-%m-%dT%H:%M")} terminal=false refresh=false'


def menu_bar(now):
    shown = [z for z in ZONES if z[2]] or ZONES
    parts = []
    for emoji, tz, _ in shown:
        t = now.astimezone(tz)
        colour = WHITE if in_hours(t, WORK) else ORANGE
        tag = emoji if emoji else f"{t.tzname()} "
        parts.append(f"{colour}{tag}{t.strftime('%H:%M')}{RESET}")
    print(" ".join(parts) + " | ansi=true size=12")


def now_section(now):
    for emoji, tz, _ in ZONES:
        t = now.astimezone(tz)
        colour = "" if in_hours(t, WORK) else " color=#FF8A65"
        print(f"{t.tzname():<5} {t.strftime('%H:%M')}  {emoji} | {MONO}{colour} {copy_action(now)}")


def table(now):
    home_now = now.astimezone(HOME)
    day = home_now.date()
    print(GAP.join(f"{now.astimezone(tz).tzname():^5}" for _, tz, _ in ZONES) + f" | {MONO} color=gray")
    for h in range(24):
        utc = datetime(day.year, day.month, day.day, h, tzinfo=HOME).astimezone(timezone.utc)
        times = [utc.astimezone(tz) for _, tz, _ in ZONES]
        if all(in_hours(t, WORK) for t in times):
            tag, colour = "   best", " color=#4CAF50"
        elif all(in_hours(t, STRETCH) for t in times):
            tag, colour = "   ok", " color=#FFB300"
        else:
            tag, colour = "", ""
        if h == home_now.hour:
            tag += "   ◀ now"
        cells = GAP.join(t.strftime("%H:%M") for t in times)
        print(f"{cells}{tag} | {MONO}{colour} {copy_action(utc)}")


def main():
    if len(sys.argv) == 3 and sys.argv[1] == "copy":
        utc = datetime.strptime(sys.argv[2], "%Y-%m-%dT%H:%M").replace(tzinfo=timezone.utc)
        subprocess.run(["pbcopy"], input=slot_text(utc).encode())
        return
    #
    now = datetime.now(timezone.utc)
    menu_bar(now)
    print("---")
    if CONFIG_ERROR:
        print("⚠️ Config error, using defaults: re-run install.py | color=#FF8A65")
        print(f"--{CONFIG_ERROR} | size=11")
    now_section(now)
    print("---")
    table(now)


if __name__ == "__main__":
    main()




#
