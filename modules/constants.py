from modules import config

# --- UI VISUALS ---
ICONS = {
    "opts": "🛠️ Menu Settings",
    "apps": "📱 Applications",
    "run": "🚀 Run",
    "back": "⬅️ BACK",
    "home": "🏠 HOME"
}

SEP_LINE = "────────────────────────────────────────"
RUN_ICON = "utilities-terminal"

# --- INTERNAL ACTIONS ---
INTERNAL_MENU = {
    "🧹 Clear History": "INTERNAL:CLEAR_HIST",
    "📝 Edit Config": f"TERM:nvim {config.CONFIG_PATH}"
}

# --- CLI HELP TEXT ---
def get_help_text(c):
    return (
        f"{c['bold']}{c['blue']}CMD-Center Launcher{c['reset']}\n"
        f"{c['yellow']}Usage:{c['reset']} cmd-center [{c['green']}apps|run|options{c['reset']}]\n\n"
        f"  {c['green']}apps{c['reset']}      Direct to Applications\n"
        f"  {c['green']}run{c['reset']}       Direct to Binary Runner\n"
        f"  {c['green']}options{c['reset']}   Direct to Settings"
    )