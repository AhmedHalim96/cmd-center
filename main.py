#!/usr/bin/env python3
import subprocess, os, sys, argparse
from modules import config, scanner, engine
from modules.constants import (
    ICONS, NAV_ICONS, SEP_LINE, RUN_ICON, 
    FOLDER_ICON, INTERNAL_MENU, get_help_text
)

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
            for cat in categories:
                cat_val = menu_data[cat]
                icon = cat_val.get("icon", FOLDER_ICON) if isinstance(cat_val, dict) else FOLDER_ICON
                rofi_list.append(f"{cat}\0icon\x1f{icon}")
            
            for mode in [ICONS["run"], ICONS["apps"], ICONS["opts"]]:
                rofi_list.append(f"{mode}\0icon\x1f{NAV_ICONS.get(mode, 'system-run')}")

            rofi_list.append(SEP_LINE)

            # Global Search Pool
            flat_user = engine.get_flat_menu(menu_data)
            flat_internal = engine.get_flat_menu(INTERNAL_MENU, prefix=ICONS["opts"])
            app_pool = {f"{n}    ({ICONS['apps']})\0icon\x1f{d['icon']}": d for n, d in scanner.get_system_apps().items()}
            run_pool = {f"{k.split('RUN:')[1]}    ({ICONS['run']})\0icon\x1f{RUN_ICON}": k.split('RUN:')[1] for k in weights.keys() if k.startswith("RUN:")}
            
            combined_pool = {**flat_user, **flat_internal, **app_pool, **run_pool}
            
            def global_sort(x):
                clean_name = x.split("\0")[0]
                if clean_name.endswith(f"({ICONS['apps']})"): return weights.get(f"APP:{clean_name.split('    (')[0]}", 0)
                if clean_name.endswith(f"({ICONS['run']})"): return weights.get(f"RUN:{clean_name.split('    (')[0]}", 0)
                return weights.get(f"HOME:{clean_name}", 0)
            
            rofi_list.extend(sorted(combined_pool.keys(), key=global_sort, reverse=True))

            # Lookup mapping for Hub
            for k in combined_pool.keys(): options_dict[k.split("\0")[0]] = k 
            for cat in menu_data: options_dict[cat] = cat
            for mode_icon in [ICONS["run"], ICONS["apps"], ICONS["opts"]]: options_dict[mode_icon] = mode_icon
        else:
            # --- SUB-MENU VIEW ---
            rofi_list.append(f"{ICONS['back']}\0icon\x1f{NAV_ICONS[ICONS['back']]}")
            if path_depth >= 2:
                rofi_list.append(f"{ICONS['home']}\0icon\x1f{NAV_ICONS[ICONS['home']]}")
            
            items = list(active_menu.keys())
            if in_apps:
                items.sort(key=lambda x: (weights.get(f"APP:{x}", 0), x.lower()), reverse=True)
                for i in items: rofi_list.append(f"{i}\0icon\x1f{active_menu[i].get('icon', 'system-run')}")
            elif in_run:
                items.sort(key=lambda x: (weights.get(f"RUN:{x}", 0), x.lower() if weights.get(f"RUN:{x}", 0) == 0 else ""), reverse=True)
                for i in items: rofi_list.append(f"{i}\0icon\x1f{RUN_ICON}")
            else:
                if not in_opts and settings.get("remember_history", True):
                    items.sort(key=lambda x: weights.get(f"{path_str}:{x}", 0), reverse=True)
                for i in items:
                    val = active_menu[i]
                    label = val.get("label", i) if isinstance(val, dict) else i
                    is_folder = isinstance(val, dict) and ("items" in val or "cmd" not in val)
                    icon = val.get("icon", FOLDER_ICON if is_folder else "system-run") if isinstance(val, dict) else (FOLDER_ICON if is_folder else "system-run")
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
            full_key = options_dict.get(choice, choice)
            if not current_path:
                selection = combined_pool.get(full_key) or menu_data.get(full_key)
            else:
                selection = active_menu.get(full_key)
            
            if selection is None and in_run: selection = choice 
            if selection is None: continue

            is_folder = isinstance(selection, dict) and ("items" in selection or "cmd" not in selection)
            if (in_apps or in_run) and not isinstance(selection, dict): is_folder = False

            if is_folder:
                current_path.append(full_key)
            else:
                is_app = "(" + ICONS["apps"] in choice_raw or in_apps
                is_run = "(" + ICONS["run"] in choice_raw or in_run
                label = choice.split("    (")[0] if (is_app or is_run) else choice
                cmd_data = selection.get("cmd", selection) if isinstance(selection, dict) else selection
                
                if settings.get("remember_history", True):
                    if is_run: w_key = f"RUN:{label}"
                    elif is_app: w_key = f"APP:{label}"
                    elif not current_path: w_key = f"HOME:{choice}"
                    else: w_key = f"{path_str}:{choice}"
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