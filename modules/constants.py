from modules import config

# --- UI VISUALS ---
ICONS = {
    "opts": "Menu Settings",
    "apps": "Applications",
    "run": "Run",
    "back": "BACK",
    "home": "HOME"
}

# Icon names for Rofi's -show-icons mode
NAV_ICONS = {
    ICONS["back"]: "go-previous",
    ICONS["home"]: "go-home",
    ICONS["opts"]: "emblem-system",
    ICONS["apps"]: "applications-all",
    ICONS["run"]: "run"
}

FOLDER_ICON = "folder"
RUN_ICON = "utilities-terminal"
SEP_LINE = "────────────────────────────────────────"

# --- INTERNAL ACTIONS ---
INTERNAL_MENU = {
    "🧹 Clear History": "INTERNAL:CLEAR_HIST",
    "📝 Edit Config": f"TERM:nvim {config.CONFIG_PATH}"
}

# --- HELP TEXT ---
def get_help_text(c):
    return (
        f"{c['bold']}{c['blue']}CMD-Center Launcher{c['reset']}\n"
        f"{c['yellow']}Usage:{c['reset']} cmd-center [{c['green']}apps|run|options{c['reset']}]\n\n"
        f"  {c['green']}apps{c['reset']}      Direct to Applications\n"
        f"  {c['green']}run{c['reset']}       Direct to Binary Runner\n"
        f"  {c['green']}options{c['reset']}   Direct to Settings"
    )