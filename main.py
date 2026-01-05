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

    while True:
        path_depth = len(current_path)
        in_run = path_depth > 0 and current_path[0] == ICONS["run"]
        in_apps = path_depth > 0 and current_path[0] == ICONS["apps"]
        in_opts = path_depth > 0 and current_path[0] == ICONS["opts"]

        # 3. Resolve Menu Source
        if in_opts: active_menu = INTERNAL_MENU
        elif in_apps: active_menu = scanner.get_system_apps()
        elif in_run:
            run_hist = {k.split("RUN:")[1]: k.split("RUN:")[1] for k in weights.keys() if k.startswith("RUN:")}
            active_menu = {**{b: b for b in scanner.get_binaries()}, **run_hist}
        else: active_menu = menu_data

        # 4. Navigate hierarchy
        try:
            start_idx = 1 if (in_opts or in_apps or in_run) else 0
            for i in range(start_idx, path_depth):
                node = active_menu[current_path[i]]
                active_menu = node.get("items", node) if isinstance(node, dict) else node
        except:
            current_path, active_menu = [], menu_data

        rofi_list, options_dict, combined_pool = [], {}, {}
        path_str = " > ".join(current_path)

        # 5. Build Rofi List
        if not current_path:
            # --- HUB VIEW ---
            categories = sorted(menu_data.keys(), key=lambda x: weights.get(f"HOME:{x}", 0), reverse=True)
            rofi_list.extend(categories + [ICONS["run"], ICONS["apps"], ICONS["opts"], SEP_LINE])

            # Prepare Search Pools
            flat_user = engine.get_flat_menu(menu_data)
            flat_internal = engine.get_flat_menu(INTERNAL_MENU, prefix=ICONS["opts"])
            app_pool = {f"{n}    ({ICONS['apps']})\0icon\x1f{d['icon']}": d for n, d in scanner.get_system_apps().items()}
            
            combined_pool = {**flat_user, **flat_internal, **app_pool}
            
            def global_sort(x):
                clean_name = x.split("\0")[0]
                if clean_name.endswith(f"({ICONS['apps']})"): return weights.get(f"APP:{clean_name.split('    (')[0]}", 0)
                return weights.get(f"HOME:{clean_name}", 0)
            
            sorted_search = sorted(combined_pool.keys(), key=global_sort, reverse=True)
            rofi_list.extend(sorted_search)
            
            # Populate Lookup Map for HUB
            for k in combined_pool.keys(): options_dict[k.split("\0")[0]] = k 
            for cat in menu_data: options_dict[cat] = cat
            for mode_icon in [ICONS["run"], ICONS["apps"], ICONS["opts"]]: options_dict[mode_icon] = mode_icon
        else:
            # --- SUB-MENU VIEW ---
            rofi_list.append(ICONS["back"])
            if path_depth >= 2: rofi_list.append(ICONS["home"])
            for i in active_menu.keys():
                val = active_menu[i]
                label = val.get("label", i) if isinstance(val, dict) else i
                icon = val.get("icon", "folder" if (isinstance(val, dict) and "items" in val) else "system-run") if isinstance(val, dict) else "system-run"
                rofi_list.append(f"{label}\0icon\x1f{icon}")
                options_dict[label] = i 

        # 6. Interaction
        prompt = f" {settings.get('prompt_icon', '⚡')} {path_str if path_str else 'HUB'} "
        proc = subprocess.run(rofi_args + ["-p", prompt], input="\n".join(rofi_list), text=True, capture_output=True)
        choice_raw = proc.stdout.strip()
        
        if not choice_raw or choice_raw == SEP_LINE:
            if not choice_raw: sys.exit(0)
            continue

        choice = choice_raw.split("\0")[0]

        # 7. Routing & Execution
        if choice == ICONS["back"]: current_path.pop()
        elif choice == ICONS["home"]: current_path = []
        elif choice in [ICONS["opts"], ICONS["apps"], ICONS["run"]]: current_path = [choice]
        else:
            # RESOLUTION LOGIC
            internal_key = options_dict.get(choice, choice)
            
            if not current_path:
                # 1. Check the Search Pool first (to handle search results)
                full_key = options_dict.get(choice)
                selection = combined_pool.get(full_key)
                # 2. If search pool is empty, check if it's a top-level category
                if selection is None:
                    selection = menu_data.get(internal_key)
            else:
                selection = active_menu.get(internal_key)
            
            if selection is None and in_run: selection = internal_key
            if selection is None: continue

            # Navigation logic
            is_folder = isinstance(selection, dict) and ("items" in selection or "cmd" not in selection)
            if (in_apps or in_run) and not isinstance(selection, dict): is_folder = False

            if is_folder:
                current_path.append(internal_key)
            else:
                # --- EXECUTION ENGINE ---
                is_app = "(" in choice_raw and ICONS["apps"] in choice_raw
                label = choice.split("    (")[0] if is_app else choice
                cmd_data = selection.get("cmd", selection) if isinstance(selection, dict) else selection
                
                if settings.get("remember_history", True):
                    w_key = f"APP:{label}" if is_app else (f"HOME:{choice}" if not current_path else f"{path_str}:{choice}")
                    weights[w_key] = weights.get(w_key, 0) + 1
                
                state["last_path"], state["history"] = (current_path, weights)
                config.save_json(config.STATE_PATH, state)

                if cmd_data == "INTERNAL:CLEAR_HIST":
                    state["history"] = {}; config.save_json(config.STATE_PATH, state); sys.exit(0)
                
                t = settings.get("terminal_emulator", "wezterm start --")
                cmd_str = str(cmd_data)
                if cmd_str.startswith("TERM:"): f_cmd = f"{t} bash -c \"{cmd_str[5:]}; echo; read\""
                elif cmd_str.startswith("EDT:"): f_cmd = f"{t} {settings.get('editor', 'nano')} {os.path.expanduser(cmd_str[4:])}"
                elif cmd_str.startswith("WEB:"): 
                    url = cmd_str[4:] if '://' in cmd_str[4:] else 'https://' + cmd_str[4:]
                    f_cmd = f"xdg-open '{url}'"
                else: f_cmd = cmd_str
                
                subprocess.Popen(f_cmd, shell=True, start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                sys.exit(0)

        state["last_path"] = current_path
        config.save_json(config.STATE_PATH, state)

if __name__ == "__main__":
    main()