from modules import config

# --- UI LABELS ---
# These are the text strings used for navigation and internal logic matching
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

# --- WEB SEARCH CONFIG ---
# Typing the key followed by a space will trigger a search in your browser
# Example: "g how to exit vim"
SEARCH_PROVIDERS = {
    "g": "https://www.google.com/search?q=",
    "y": "https://www.youtube.com/results?search_query=",
    "gh": "https://github.com/search?q=",
    "w": "https://en.wikipedia.org/wiki/Special:Search?search=",
    "r": "https://www.reddit.com/search/?q=",
    "amz": "https://www.amazon.com/s?k="
}

# --- SMART LAUNCHER CONFIG ---
# Binaries in this list will automatically open in a terminal window.
CLI_ONLY = [
    "htop", "btop", "nvtop", "atop", "vim", "nvim", "nano", 
    "ranger", "nmap", "ssh", "ping", "top", "gdb", "python",
    "ipython", "ncdu", "journalctl", "dmesg", "glances", "tail"
]

# --- INTERNAL ACTIONS ---
# Fixed commands for the 'Menu Settings' section
INTERNAL_MENU = {
    "❓ Help & Keybinds": "INTERNAL:HELP",  # New help command
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




def get_internal_help():
    """Generates a clean, aligned plain-text help screen"""
    lines = [
        "╔══════════════════════════════════════════════════════════╗",
        "║                COMMAND CENTER QUICK START                ║",
        "╚══════════════════════════════════════════════════════════╝",
        "",
        " ■ WEB SEARCHES",
        "   Type the prefix followed by your query:",
        "   --------------------------------------------------------"
    ]
    
    for key, url in SEARCH_PROVIDERS.items():
        domain = url.split('//')[1].split('/')[0]
        lines.append(f"   {key.ljust(4)} ->  {domain}")
    
    lines.append("")
    lines.append(" ■ COMMAND PREFIXES")
    lines.append("   TERM:  Forces command to run in a Terminal window")
    lines.append("   WEB:   Forces string to open as a URL in Browser")
    lines.append("")
    lines.append(" ■ AUTO-TERMINAL APPLICATIONS")
    lines.append("   The following run in terminal automatically:")
    lines.append("   --------------------------------------------------------")
    
    # Wrap the CLI list so it doesn't go off screen
    cli_apps = sorted(CLI_ONLY)
    for i in range(0, len(cli_apps), 4):
        lines.append("   " + ", ".join(cli_apps[i:i+4]))
        
    lines.append("\n [ Press ESC or click Close to return to Menu ]")
    
    return "\n".join(lines)