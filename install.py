#!/usr/bin/env python3
"""Interactive setup: pick your time zones + emojis, then drop the plugin into SwiftBar.

Re-run any time to change zones; your current picks are the defaults.
    python3 install.py              # wizard, then install the plugin
    python3 install.py --no-install # wizard only (just rewrite the config)
"""
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, available_timezones

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN = "timezones.1s.py"
CONFIG = os.path.expanduser("~/.config/swiftbar-timezones/config.json")
LINK = os.path.expanduser("~/.local/bin/tz-planner")
# (city, tz, suggested emoji) — the quick-pick list
COMMON = [
    ("Honolulu", "Pacific/Honolulu", "🌺"),
    ("Anchorage", "America/Anchorage", "🐻"),
    ("Los Angeles / San Francisco", "America/Los_Angeles", "🌴"),
    ("Denver", "America/Denver", "🏔️"),
    ("Phoenix", "America/Phoenix", "🌵"),
    ("Chicago", "America/Chicago", "🌆"),
    ("New York / Toronto", "America/New_York", "🗽"),
    ("Mexico City", "America/Mexico_City", "🇲🇽"),
    ("São Paulo", "America/Sao_Paulo", "🇧🇷"),
    ("UTC", "UTC", "🌐"),
    ("London", "Europe/London", "🇬🇧"),
    ("Dublin", "Europe/Dublin", "🇮🇪"),
    ("Lisbon", "Europe/Lisbon", "🇵🇹"),
    ("Paris", "Europe/Paris", "🇫🇷"),
    ("Amsterdam", "Europe/Amsterdam", "🇳🇱"),
    ("Berlin", "Europe/Berlin", "🇩🇪"),
    ("Madrid", "Europe/Madrid", "🇪🇸"),
    ("Stockholm", "Europe/Stockholm", "🇸🇪"),
    ("Athens", "Europe/Athens", "🇬🇷"),
    ("Johannesburg", "Africa/Johannesburg", "🇿🇦"),
    ("Dubai", "Asia/Dubai", "🇦🇪"),
    ("India", "Asia/Kolkata", "🇮🇳"),
    ("Singapore", "Asia/Singapore", "🇸🇬"),
    ("Hong Kong", "Asia/Hong_Kong", "🇭🇰"),
    ("Shanghai", "Asia/Shanghai", "🇨🇳"),
    ("Tokyo", "Asia/Tokyo", "🇯🇵"),
    ("Seoul", "Asia/Seoul", "🇰🇷"),
    ("Sydney / Melbourne", "Australia/Sydney", "🇦🇺"),
    ("Auckland", "Pacific/Auckland", "🇳🇿"),
]
SUGGEST = {tz: emoji for _, tz, emoji in COMMON}
BOLD, DIM, ORANGE, RESET = "\033[1m", "\033[2m", "\033[38;5;209m", "\033[0m"


def ask(prompt, default=""):
    shown = f" {DIM}[{default}]{RESET}" if default != "" else ""
    try:
        ans = input(f"{prompt}{shown}: ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\nCancelled, nothing changed.")
        sys.exit(1)
    return ans if ans else default


def yes(prompt, default=True):
    while True:
        ans = ask(f"{prompt} (y/n)", "y" if default else "n").lower()
        if ans in ("y", "yes", "n", "no"):
            return ans.startswith("y")


def offset_hours(tz):
    return datetime.now(timezone.utc).astimezone(ZoneInfo(tz)).utcoffset().total_seconds() / 3600


def describe(tz):
    t = datetime.now(timezone.utc).astimezone(ZoneInfo(tz))
    off = offset_hours(tz)
    return f"{tz}  {DIM}{t.tzname()}, UTC{off:+g}, now {t.strftime('%H:%M')}{RESET}"


def system_tz():
    try:
        return os.readlink("/etc/localtime").split("zoneinfo/")[-1]
    except OSError:
        return "UTC"


def load_existing():
    try:
        with open(CONFIG) as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def search(term):
    """Resolve one typed city/zone name to a tz, asking if several match."""
    key = term.lower().replace(" ", "_")
    hits = [tz for _, tz, _ in COMMON if key in tz.lower()]
    hits += [c_tz for city, c_tz, _ in COMMON if term.lower() in city.lower() and c_tz not in hits]
    if not hits:
        hits = sorted(tz for tz in available_timezones() if key in tz.lower() and "/" in tz and not tz.startswith(("Etc/", "SystemV/")))
    if not hits:
        print(f"  {ORANGE}No zone matches '{term}'.{RESET} Try a big nearby city, e.g. 'Chicago' or 'Kolkata'.")
        return None
    if len(hits) == 1:
        return hits[0]
    hits = hits[:15]
    print(f"  '{term}' matches several:")
    for i, tz in enumerate(hits, 1):
        print(f"   {i:>2}. {describe(tz)}")
    pick = ask("  Which one (number, blank to skip)")
    return hits[int(pick) - 1] if pick.isdigit() and 1 <= int(pick) <= len(hits) else None


def pick_zones(current):
    print(f"\n{BOLD}1. Which time zones do you want to track?{RESET}\n")
    half = (len(COMMON) + 1) // 2
    for i in range(half):
        left = f"{i + 1:>2}. {COMMON[i][2]} {COMMON[i][0]}"
        right = f"{i + half + 1:>2}. {COMMON[i + half][2]} {COMMON[i + half][0]}" if i + half < len(COMMON) else ""
        print(f"  {left:<36}{right}")
    print(f"\nType numbers and/or any city or zone name, separated by commas.")
    print(f"{DIM}e.g.  3, 7, 11   or   3, 7, Kolkata, Europe/Warsaw{RESET}")
    default = ", ".join(current) if current else ""
    while True:
        raw = ask("Zones", default)
        chosen = []
        for token in raw.replace(";", ",").split(","):
            for part in token.split() if token.strip().replace(" ", "").isdigit() else [token.strip()]:
                if not part:
                    continue
                if part.isdigit():
                    n = int(part)
                    tz = COMMON[n - 1][1] if 1 <= n <= len(COMMON) else None
                    if tz is None:
                        print(f"  {ORANGE}{n} isn't on the list.{RESET}")
                elif part in available_timezones():
                    tz = part
                else:
                    tz = search(part)
                if tz and tz not in chosen:
                    chosen.append(tz)
        if chosen:
            return sorted(chosen, key=offset_hours)  # west to east
        print(f"  {ORANGE}Pick at least one zone.{RESET}")


def pick_details(zones, existing):
    old = {z["tz"]: z for z in (existing or {}).get("zones", [])}
    print(f"\n{BOLD}2. Emoji and menu bar spot for each zone{RESET}")
    print(f"{DIM}Enter keeps the suggestion. Paste any emoji (Ctrl+Cmd+Space opens the picker), or '-' for none (shows e.g. 'EST' instead).{RESET}")
    if len(zones) > 4:
        print(f"{DIM}Tip: the menu bar gets crowded past 3-4 zones; the rest still show in the dropdown.{RESET}")
    out = []
    for i, tz in enumerate(zones):
        print(f"\n  {describe(tz)}")
        prev = old.get(tz, {})
        emoji = ask("  Emoji", prev.get("emoji") or SUGGEST.get(tz, "-"))
        emoji = "" if emoji == "-" else emoji
        menubar = yes("  Show in the menu bar", prev.get("menubar", i < 4))
        out.append({"tz": tz, "emoji": emoji, "menubar": menubar})
    if not any(z["menubar"] for z in out):
        print(f"  {DIM}None picked for the menu bar, so showing them all.{RESET}")
        for z in out:
            z["menubar"] = True
    return out


def pick_home(zones, existing):
    print(f"\n{BOLD}3. Home zone{RESET} {DIM}(the 24-hour planner runs midnight to midnight in this zone){RESET}")
    for i, z in enumerate(zones, 1):
        print(f"   {i}. {z['emoji']} {describe(z['tz'])}")
    tzs = [z["tz"] for z in zones]
    prev = (existing or {}).get("home")
    default = tzs.index(prev) + 1 if prev in tzs else (tzs.index(system_tz()) + 1 if system_tz() in tzs else 1)
    while True:
        n = ask("Home", str(default))
        if n.isdigit() and 1 <= int(n) <= len(zones):
            return tzs[int(n) - 1]


def pick_hours(label, default):
    while True:
        raw = ask(label, f"{default[0]}-{default[1]}").replace(" ", "")
        try:
            a, b = (int(x) for x in raw.split("-"))
            if 0 <= a < b <= 24:
                return [a, b]
        except ValueError:
            pass
        print(f"  {ORANGE}Use start-end in whole hours, e.g. 9-17.{RESET}")


def preview(cfg):
    now = datetime.now(timezone.utc)
    parts = []
    for z in cfg["zones"]:
        if not z["menubar"]:
            continue
        t = now.astimezone(ZoneInfo(z["tz"]))
        out = not (cfg["work"][0] <= t.hour < cfg["work"][1])
        tag = z["emoji"] or f"{t.tzname()} "
        parts.append(f"{ORANGE if out else ''}{tag}{t.strftime('%H:%M')}{RESET}")
    return " ".join(parts)


def install_plugin():
    try:
        folder = subprocess.run(["defaults", "read", "com.ameba.SwiftBar", "PluginDirectory"], capture_output=True, text=True).stdout.strip()
    except OSError:
        folder = ""
    if not folder or not os.path.isdir(os.path.expanduser(folder)):
        print(f"\n{ORANGE}Couldn't find SwiftBar's plugin folder.{RESET} Install SwiftBar (brew install --cask swiftbar),")
        print(f"open it once to choose a folder, then re-run this - or copy {PLUGIN} there yourself.")
        return
    folder = os.path.expanduser(folder)
    dest = os.path.join(folder, PLUGIN)
    if not yes(f"\nInstall the plugin to {dest}"):
        return
    shutil.copy2(os.path.join(HERE, PLUGIN), dest)
    os.chmod(dest, 0o755)
    # SwiftBar's click-to-copy breaks on paths with spaces, so give it a space-free link
    if " " in dest:
        os.makedirs(os.path.dirname(LINK), exist_ok=True)
        if os.path.islink(LINK) or os.path.exists(LINK):
            os.remove(LINK)
        os.symlink(dest, LINK)
    print(f"Installed. {DIM}SwiftBar picks it up within a few seconds.{RESET}")


def main():
    existing = load_existing()
    print(f"{BOLD}SwiftBar Timezones setup{RESET}")
    if existing:
        print(f"{DIM}Editing your current setup ({CONFIG}); Enter keeps each answer.{RESET}")
    current = [z["tz"] for z in existing["zones"]] if existing else []
    zones = pick_zones(current)
    details = pick_details(zones, existing)
    home = pick_home(details, existing)
    print(f"\n{BOLD}4. Hours{RESET} {DIM}(times outside work hours turn orange; the planner marks slots 'best' if every zone is in work hours, 'ok' if all are in stretch hours){RESET}")
    work = pick_hours("Work hours", (existing or {}).get("work", [9, 17]))
    stretch = pick_hours("Stretch hours", (existing or {}).get("stretch", [8, 18]))
    cfg = {"home": home, "work": work, "stretch": stretch, "zones": details}
    print(f"\nMenu bar will look like:  {preview(cfg)}")
    if not yes("Save this"):
        print("Nothing saved.")
        return
    os.makedirs(os.path.dirname(CONFIG), exist_ok=True)
    with open(CONFIG, "w") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)
    print(f"Saved {CONFIG}")
    if "--no-install" not in sys.argv:
        install_plugin()
    subprocess.run(["open", "-g", "swiftbar://refreshallplugins"], capture_output=True)


if __name__ == "__main__":
    main()




#
