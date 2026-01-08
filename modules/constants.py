from modules import config

# --- UI LABELS ---
# These are the text strings used for navigation and matching
ICONS = {
    "opts": "Menu Settings",
    "apps": "Applications",
    "run": "Run",
    "back": "BACK",
    "home": "HOME"
}

# --- ICON MAPPING ---
# Icon names for Rofi's -show-icons mode. 
# Set a value to "" to make it blank/text-only.
NAV_ICONS = {
    ICONS["back"]: "go-previous",
    ICONS["home"]: "go-home",
    ICONS["opts"]: "emblem-system",
    ICONS["apps"]: "applications-all",
    ICONS["run"]: "run"
}

# Default icons for general items
FOLDER_ICON = "folder"
RUN_ICON = "utilities-terminal"
SEP_LINE = "────────────────────────────────────────"

# --- PROMPT VISUALS ---
# The symbol shown in the Rofi prompt bar based on your location
PROMPT_ICONS = {
    "HUB": "⚡",              # Main Screen
    ICONS["apps"]: "📱",      # Applications Mode
    ICONS["run"]: "🚀",       # Run/Binary Mode
    ICONS["opts"]: "🛠️",      # Settings Mode
    "DEFAULT": "📂"           # Custom Categories
}

# --- SMART LAUNCHER CONFIG ---
# Binaries in this list will automatically open in a terminal window.
# You can add any CLI tools you use frequently here.
CLI_ONLY = [
    "htop", "btop", "nvtop", "atop", "vim", "nvim", "nano", 
    "ranger", "nmap", "ssh", "ping", "top", "gdb", "python",
    "ipython", "ncdu", "journalctl", "dmesg", "htop", "glances"
]

# --- INTERNAL ACTIONS ---
# Fixed commands for the 'Menu Settings' section
INTERNAL_MENU = {
    "🧹 Clear History": "INTERNAL:CLEAR_HIST",
    "📝 Edit Config": f"TERM:nvim {config.CONFIG_PATH}"
}

# --- HELP TEXT ---
# Displayed when running with --help
def get_help_text(c):
    return (
        f"{c['bold']}{c['blue']}CMD-Center Launcher{c['reset']}\n"
        f"{c['yellow']}Usage:{c['reset']} cmd-center [{c['green']}apps|run|options{c['reset']}]\n\n"
        f"  {c['green']}apps{c['reset']}      Direct to Applications\n"
        f"  {c['green']}run{c['reset']}       Direct to Binary Runner\n"
        f"  {c['green']}options{c['reset']}   Direct to Settings"
    )