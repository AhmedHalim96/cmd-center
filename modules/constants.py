from modules import config

# --- UI LABELS ---
# These include the Icon and the Label for the unified "Icon Label" look.
ICONS = {
    "opts": "⚙️️️ Menu Settings",
    "apps": "📱 Applications",
    "run": "🚀 Run Command",
    "config": "📝 Config Editor",
    "back": "⬅ BACK",
    "home": "🏠 HOME",
}

# --- ICON MAPPING ---
# Maps the UI labels to internal system icon names for Rofi's -show-icons mode.
NAV_ICONS = {
    ICONS["back"]: "go-previous",
    ICONS["home"]: "go-home",
    ICONS["opts"]: "emblem-system",
    ICONS["apps"]: "applications-all",
    ICONS["run"]: "utilities-terminal",
    ICONS["config"]: "accessories-text-editor"
}

# Default icons for general items
FOLDER_ICON = ""
RUN_ICON = "utilities-terminal"
SEP_LINE = "────────────────────────────────────────"

# --- PROMPT VISUALS ---
# The symbol shown in the Rofi prompt bar based on your location
PROMPT_ICONS = {
    "HUB": "✨",                 # Main Screen
    ICONS["apps"]: "📱",        # Applications Mode
    ICONS["run"]: "🚀",          # Run/Binary Mode
    ICONS["config"]: "📝",    # Config Editor
    ICONS["opts"]: "⚙️",        # Settings Mode
    "DEFAULT": "📂"                 # Custom Categories
}

# --- WEB SEARCH CONFIG ---
SEARCH_PROVIDERS = {
    "g": "https://www.google.com/search?q=",
    "y": "https://www.youtube.com/results?search_query=",
    "gh": "https://github.com/search?q=",
    "w": "https://en.wikipedia.org/wiki/Special:Search?search=",
    "r": "https://www.reddit.com/search/?q=",
    "amz": "https://www.amazon.com/s?k="
}

# --- SMART LAUNCHER CONFIG ---
CLI_ONLY = [
    "htop", "btop", "nvtop", "atop", "vim", "nvim", "nano", 
    "ranger", "nmap", "ssh", "ping", "top", "gdb", "python",
    "ipython", "ncdu", "journalctl", "dmesg", "glances", "tail"
]

# --- INTERNAL ACTIONS ---
INTERNAL_MENU = {
    "❓ Help & Keybinds": "INTERNAL:HELP",
    "🧹 Clear History": "INTERNAL:CLEAR_HIST",
}

# --- HELP TEXT ---
def get_help_text(c):
    return (
        f"{c['bold']}{c['blue']}CMD-Center Launcher{c['reset']}\n"
        f"{c['yellow']}Usage:{c['reset']} cmd-center [{c['green']}apps|run|config|options{c['reset']}]\n\n"
        f"  {c['green']}apps{c['reset']}      Direct to Applications\n"
        f"  {c['green']}run{c['reset']}       Direct to Binary Runner\n"
        f"  {c['green']}config{c['reset']}    Direct to Config Editor\n"
        f"  {c['green']}options{c['reset']}   Direct to Settings"
    )

def get_internal_help():
    """Generates a clean, aligned plain-text help screen"""
    lines = [
        "╔══════════════════════════════════════════════════════════╗",
        "║                COMMAND CENTER QUICK START                ║",
        "╚══════════════════════════════════════════════════════════╝",
        "",
        " ■ MODES",
        f"   {ICONS['apps'].ljust(20)} -> Browse system desktop files",
        f"   {ICONS['run'].ljust(20)} -> Execute binaries with history",
        f"   {ICONS['config'].ljust(20)} -> Edit defined config files",
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
    lines.append("   EDT:   Opens file in terminal editor (Config Mode)")
    lines.append("")
    lines.append(" ■ AUTO-TERMINAL APPLICATIONS")
    lines.append("   The following run in terminal automatically:")
    lines.append("   --------------------------------------------------------")
    
    cli_apps = sorted(CLI_ONLY)
    for i in range(0, len(cli_apps), 4):
        lines.append("   " + ", ".join(cli_apps[i:i+4]))
        
    lines.append("\n [ Press ESC or click Close to return to Menu ]")
    
    return "\n".join(lines)