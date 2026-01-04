#!/usr/bin/env python3
import subprocess, os, sys, argparse
from modules import config, scanner, engine

# --- UI CONSTANTS ---
ICONS = {
    "opts": "🛠️ Menu Settings",
    "apps": "📱 Applications",
    "run": "🚀 Run",
    "back": "⬅️ BACK",
    "home": "🏠 HOME"
}
SEP_LINE = "────────────────────────────────────────"
RUN_ICON = "utilities-terminal"

INTERNAL_MENU = {
    "🧹 Clear History": "INTERNAL:CLEAR_HIST",
    "📝 Edit Config": f"TERM:nvim {config.CONFIG_PATH}"
}

def main():
    # 1. Setup CLI Arguments & Colors
    c = config.get_colors()
    parser = argparse.ArgumentParser(description="CMD-Center Launcher", usage=argparse.SUPPRESS)
    parser.add_argument('mode', nargs='?', choices=['apps', 'run', 'options'])
    
    if len(sys.argv) > 1 and sys.argv[1] in ["-h", "--help"]:
        print(f"{c['bold']}{c['blue']}CMD-Center Launcher{c['reset']}")
        print(f"{c['yellow']}Usage:{c['reset']} cmd-center [{c['green']}apps|run|options{c['reset']}]\n")
        print(f"  {c['green']}apps{c['reset']}      Direct to Applications")
        print(f"  {c['green']}run{c['reset']}       Direct to Binary Runner")
        print(f"  {c['green']}options{c['reset']}   Direct to Settings")
        sys.exit(0)

    args = parser.parse_args()

    # 2. Load Data
    cfg_data = config.load_json(config.CONFIG_PATH)
    state = config.load_json(config.STATE_PATH)
    settings = cfg_data.get("settings", {})
    menu_data = cfg_data.get("menu", {})
    weights = state.get("history", {}) if settings.get("remember_history", True) else {}

    # Initial Path resolution
    current_path = []
    if args.mode:
        mapping = {"apps": ICONS["apps"], "run": ICONS["run"], "options": ICONS["opts"]}
        current_path = [mapping[args.mode]]
    elif settings.get("remember_last_path", True):
        current_path = state.get("last_path", [])

    rofi_args = engine.build_rofi_args(settings)

    # 3. Main Loop
    while True:
        in_run = len(current_path) > 0 and current_path[0] == ICONS["run"]
        in_apps = len(current_path) > 0 and current_path[0] == ICONS["apps"]
        in_opts = len(current_path) > 0 and current_path[0] == ICONS["opts"]

        system_apps = scanner.get_system_apps()
        
        # Resolve active menu level
        if in_opts: active_menu = INTERNAL_MENU
        elif in_apps: active_menu = system_apps
        elif in_run:
            run_hist = {k.split("RUN:")[1]: k.split("RUN:")[1] for k in weights.keys() if k.startswith("RUN:")}
            active_menu = {**{b: b for b in scanner.get_binaries()}, **run_hist}
        else: active_menu = menu_data

        try:
            depth = 1 if (in_opts or in_apps or in_run) else 0
            for i in range(depth, len(current_path)):
                active_menu = active_menu[current_path[i]]
        except:
            current_path = []; active_menu = menu_data

        path_str = " > ".join(current_path)
        rofi_list, options_dict = [], {}

        if not current_path:
            # --- HUB VIEW ---
            categories = sorted(menu_data.keys(), key=lambda x: weights.get(f"HOME:{x}", 0), reverse=True)
            rofi_list.extend(categories + [ICONS["run"], ICONS["apps"], ICONS["opts"], SEP_LINE])

            flat_user = engine.get_flat_menu(menu_data)
            app_pool = {f"{n}    ({ICONS['apps']})": d for n, d in system_apps.items()}
            run_pool = {f"{k.split('RUN:')[1]}    ({ICONS['run']})": k.split('RUN:')[1] for k in weights.keys() if k.startswith("RUN:")}
            
            combined_pool = {**flat_user, **app_pool, **run_pool}
            
            def global_sort(x):
                if x.endswith(f"({ICONS['apps']})"): return weights.get(f"APP:{x.split('    (')[0]}", 0)
                if x.endswith(f"({ICONS['run']})"): return weights.get(f"RUN:{x.split('    (')[0]}", 0)
                return weights.get(f"HOME:{x}", 0)
            
            global_items = sorted(combined_pool.keys(), key=global_sort, reverse=True)
            rofi_list.extend(global_items)
            options_dict = {**combined_pool, **menu_data}
        else:
            # --- SUB-MENU VIEW ---
            rofi_list.append(ICONS["back"])
            if len(current_path) >= 2: rofi_list.append(ICONS["home"])
            
            items = list(active_menu.keys())
            if in_apps:
                items.sort(key=lambda x: (weights.get(f"APP:{x}", 0), x.lower()), reverse=True)
                for item in items: rofi_list.append(f"{item}\0icon\x1f{active_menu[item].get('icon', 'system-run')}")
            elif in_run:
                items.sort(key=lambda x: (weights.get(f"RUN:{x}", 0), x.lower() if weights.get(f"RUN:{x}", 0) == 0 else ""), reverse=True)
                for item in items: rofi_list.append(f"{item}\0icon\x1f{RUN_ICON}")
            else:
                if not in_opts and settings.get("remember_history", True):
                    items.sort(key=lambda x: weights.get(f"{path_str}:{x}", 0), reverse=True)
                rofi_list.extend(items)

        # 4. Interaction
        prompt = f" {settings.get('prompt_icon', '⚡')} {path_str if path_str else 'HUB'} "
        proc = subprocess.run(rofi_args + ["-p", prompt], input="\n".join(rofi_list), text=True, capture_output=True)
        choice = proc.stdout.strip()

        # Handle ESC or empty return - kills the process immediately
        if not choice:
            sys.exit(0)

        if choice == SEP_LINE:
            continue

        if choice == ICONS["back"]:
            current_path.pop()
        elif choice == ICONS["home"]:
            current_path = []
        elif choice in [ICONS["opts"], ICONS["apps"], ICONS["run"]]:
            current_path = [choice]
        else:
            selection = options_dict.get(choice) if not current_path else active_menu.get(choice)
            if selection is None and in_run: selection = choice
            if selection is None: continue

            # Navigation Check
            if isinstance(selection, dict) and "cmd" not in selection:
                current_path.append(choice)
            else:
                # --- EXECUTION BLOCK ---
                is_app = "    (" + ICONS["apps"] in choice or in_apps
                is_run = "    (" + ICONS["run"] in choice or in_run
                label = choice.split("    (")[0] if (is_app or is_run) else choice
                cmd = selection["cmd"] if (isinstance(selection, dict) and "cmd" in selection) else selection
                
                # Update weights and state
                if settings.get("remember_history", True):
                    w_key = f"RUN:{label}" if is_run else (f"APP:{label}" if is_app else (f"HOME:{choice}" if not current_path else f"{path_str}:{choice}"))
                    weights[w_key] = weights.get(w_key, 0) + 1
                
                state["last_path"], state["history"] = (current_path, weights)
                config.save_json(config.STATE_PATH, state)

                if cmd == "INTERNAL:CLEAR_HIST":
                    state["history"] = {}; weights = {}; current_path = []
                    config.save_json(config.STATE_PATH, state)
                    # For clearing history, we might want to stay in the menu or exit. Let's exit.
                    sys.exit(0)
                else:
                    t = settings.get("terminal_emulator", "wezterm start --")
                    if cmd.startswith("TERM:"): cmd = f"{t} bash -c \"{cmd[5:]}; echo; read\""
                    elif cmd.startswith("EDT:"): cmd = f"{t} {settings.get('editor', 'nano')} {os.path.expanduser(cmd[4:])}"
                    elif cmd.startswith("WEB:"): cmd = f"xdg-open '{cmd[4:] if '://' in cmd[4:] else 'https://' + cmd[4:]}'"
                    
                    # Launch and detach
                    subprocess.Popen(cmd, shell=True, start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    
                    # Exit script immediately after launch to prevent re-opening Rofi
                    sys.exit(0)

if __name__ == "__main__":
    main()