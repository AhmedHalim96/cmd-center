#!/usr/bin/env python3
import subprocess, os, sys, argparse
from modules import config, scanner, engine
from modules.constants import ICONS, SEP_LINE, RUN_ICON, INTERNAL_MENU, get_help_text

def main():
    # 1. Setup & Data Loading
    c = config.get_colors()
    parser = argparse.ArgumentParser(usage=argparse.SUPPRESS)
    parser.add_argument('mode', nargs='?', choices=['apps', 'run', 'options'])
    
    if len(sys.argv) > 1 and sys.argv[1] in ["-h", "--help"]:
        print(get_help_text(c))
        sys.exit(0)

    args = parser.parse_args()
    cfg_data = config.load_json(config.CONFIG_PATH)
    state = config.load_json(config.STATE_PATH)
    
    settings = cfg_data.get("settings", {})
    menu_data = cfg_data.get("menu", {})
    weights = state.get("history", {}) if settings.get("remember_history", True) else {}

    # 2. Path Resolution
    current_path = []
    if args.mode:
        mapping = {"apps": ICONS["apps"], "run": ICONS["run"], "options": ICONS["opts"]}
        current_path = [mapping[args.mode]]
    elif settings.get("remember_last_path", True):
        current_path = state.get("last_path", [])

    rofi_args = engine.build_rofi_args(settings)

    # 3. Execution Loop
    while True:
        path_depth = len(current_path)
        in_run = path_depth > 0 and current_path[0] == ICONS["run"]
        in_apps = path_depth > 0 and current_path[0] == ICONS["apps"]
        in_opts = path_depth > 0 and current_path[0] == ICONS["opts"]

        # Resolve Menu Source
        if in_opts: active_menu = INTERNAL_MENU
        elif in_apps: active_menu = scanner.get_system_apps()
        elif in_run:
            run_hist = {k.split("RUN:")[1]: k.split("RUN:")[1] for k in weights.keys() if k.startswith("RUN:")}
            active_menu = {**{b: b for b in scanner.get_binaries()}, **run_hist}
        else: active_menu = menu_data

        # Navigate to current path
        try:
            start_idx = 1 if (in_opts or in_apps or in_run) else 0
            for i in range(start_idx, path_depth):
                active_menu = active_menu[current_path[i]]
        except:
            current_path, active_menu = [], menu_data

        # 4. Build Rofi Display
        rofi_list, options_dict = [], {}
        path_str = " > ".join(current_path)

        if not current_path:
            # HUB VIEW
            categories = sorted(menu_data.keys(), key=lambda x: weights.get(f"HOME:{x}", 0), reverse=True)
            rofi_list.extend(categories + [ICONS["run"], ICONS["apps"], ICONS["opts"], SEP_LINE])

            combined_pool = {
                **engine.get_flat_menu(menu_data), 
                **{f"{n}    ({ICONS['apps']})": d for n, d in scanner.get_system_apps().items()},
                **{f"{k.split('RUN:')[1]}    ({ICONS['run']})": k.split('RUN:')[1] for k in weights.keys() if k.startswith("RUN:")}
            }
            
            def global_sort(x):
                if x.endswith(f"({ICONS['apps']})"): return weights.get(f"APP:{x.split('    (')[0]}", 0)
                if x.endswith(f"({ICONS['run']})"): return weights.get(f"RUN:{x.split('    (')[0]}", 0)
                return weights.get(f"HOME:{x}", 0)
            
            rofi_list.extend(sorted(combined_pool.keys(), key=global_sort, reverse=True))
            options_dict = {**combined_pool, **menu_data}
        else:
            # SUB-MENU VIEW
            rofi_list.append(ICONS["back"])
            if path_depth >= 2: rofi_list.append(ICONS["home"])
            
            items = list(active_menu.keys())
            if in_apps:
                items.sort(key=lambda x: (weights.get(f"APP:{x}", 0), x.lower()), reverse=True)
                rofi_list.extend([f"{i}\0icon\x1f{active_menu[i].get('icon', 'system-run')}" for i in items])
            elif in_run:
                items.sort(key=lambda x: (weights.get(f"RUN:{x}", 0), x.lower() if weights.get(f"RUN:{x}", 0) == 0 else ""), reverse=True)
                rofi_list.extend([f"{i}\0icon\x1f{RUN_ICON}" for i in items])
            else:
                if not in_opts and settings.get("remember_history", True):
                    items.sort(key=lambda x: weights.get(f"{path_str}:{x}", 0), reverse=True)
                rofi_list.extend(items)

        # 5. User Selection
        prompt = f" {settings.get('prompt_icon', '⚡')} {path_str if path_str else 'HUB'} "
        proc = subprocess.run(rofi_args + ["-p", prompt], input="\n".join(rofi_list), text=True, capture_output=True)
        choice = proc.stdout.strip()

        if not choice or choice == SEP_LINE:
            if not choice: sys.exit(0)
            continue

        # 6. Routing & Execution
        if choice == ICONS["back"]: current_path.pop()
        elif choice == ICONS["home"]: current_path = []
        elif choice in [ICONS["opts"], ICONS["apps"], ICONS["run"]]: current_path = [choice]
        else:
            selection = options_dict.get(choice) if not current_path else active_menu.get(choice)
            if selection is None and in_run: selection = choice
            if selection is None: continue

            if isinstance(selection, dict) and "cmd" not in selection:
                current_path.append(choice)
            else:
                # EXECUTION
                is_app, is_run = "(" + ICONS["apps"] in choice or in_apps, "(" + ICONS["run"] in choice or in_run
                label = choice.split("    (")[0] if (is_app or is_run) else choice
                cmd = selection["cmd"] if (isinstance(selection, dict) and "cmd" in selection) else selection
                
                if settings.get("remember_history", True):
                    w_key = f"RUN:{label}" if is_run else (f"APP:{label}" if is_app else (f"HOME:{choice}" if not current_path else f"{path_str}:{choice}"))
                    weights[w_key] = weights.get(w_key, 0) + 1
                
                state["last_path"], state["history"] = (current_path, weights)
                config.save_json(config.STATE_PATH, state)

                if cmd == "INTERNAL:CLEAR_HIST":
                    state["history"] = {}; config.save_json(config.STATE_PATH, state)
                    sys.exit(0)
                
                t = settings.get("terminal_emulator", "wezterm start --")
                if cmd.startswith("TERM:"): cmd = f"{t} bash -c \"{cmd[5:]}; echo; read\""
                elif cmd.startswith("EDT:"): cmd = f"{t} {settings.get('editor', 'nano')} {os.path.expanduser(cmd[4:])}"
                elif cmd.startswith("WEB:"): cmd = f"xdg-open '{cmd[4:] if '://' in cmd[4:] else 'https://' + cmd[4:]}'"
                
                subprocess.Popen(cmd, shell=True, start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                sys.exit(0)

if __name__ == "__main__":
    main()