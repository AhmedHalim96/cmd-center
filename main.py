#!/usr/bin/env python3
import subprocess, os, sys, argparse, tempfile
from modules import config, scanner, engine
from modules.constants import (
    LABELS, NAV_ICONS, PROMPT_ICONS, SEP_LINE, RUN_ICON, 
    FOLDER_ICON, INTERNAL_MENU, CLI_ONLY, SEARCH_PROVIDERS, 
    get_help_text, get_internal_help
)

def main():
    # 1. Setup & Data Loading
    c = config.get_colors()
    parser = argparse.ArgumentParser(usage=argparse.SUPPRESS)
    parser.add_argument('mode', nargs='?', choices=['apps', 'run', 'config', 'options'])
    
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
        mapping = {"apps": LABELS["apps"], "run": LABELS["run"], "config": LABELS["config"], "options": LABELS["opts"]}
        current_path = [mapping[args.mode]]
    elif settings.get("remember_last_path", True):
        current_path = state.get("last_path", [])

    while True:
        path_depth = len(current_path)
        is_direct_mode = len(sys.argv) > 1 and sys.argv[1] in ["apps", "run", "config", "options"]
        in_run = path_depth > 0 and current_path[0] == LABELS["run"]
        in_apps = path_depth > 0 and current_path[0] == LABELS["apps"]
        in_opts = path_depth > 0 and current_path[0] == LABELS["opts"]
        in_config = path_depth > 0 and current_path[0] == LABELS["config"]

        show_icons = in_apps or settings.get("show_icons_globally", False)
        rofi_base_cmd = engine.build_rofi_args(settings, enable_icons=show_icons)

        # 3. Resolve Menu Source
        if in_opts: 
            active_menu = INTERNAL_MENU
        elif in_apps: 
            active_menu = scanner.get_system_apps()
        elif in_run:
            run_hist = {k.split("RUN:")[1]: k.split("RUN:")[1] for k in weights.keys() if k.startswith("RUN:")}
            active_menu = {**{b: b for b in scanner.get_binaries()}, **run_hist}
        elif in_config:
            paths_to_scan = ['~/.config/cmd-center/config.json', *settings.get("editor_paths", [])]
            config_files = {}
            for p in paths_to_scan:
                full_b = os.path.expanduser(p)
                if not os.path.exists(full_b): continue
                if os.path.isfile(full_b): 
                    config_files[full_b] = f"EDT:{full_b}"
                else:
                    for r, _, fs in os.walk(full_b):
                        if any(x in r for x in ['.git', 'node_modules', 'cache']): continue
                        for f in fs:
                            fp = os.path.join(r, f)
                            config_files[fp] = f"EDT:{fp}"
            active_menu = config_files
        else: 
            active_menu = menu_data

        # 4. Navigate Hierarchy
        try:
            start_idx = 1 if (in_opts or in_apps or in_run or in_config) else 0
            for i in range(start_idx, path_depth):
                node = active_menu[current_path[i]]
                active_menu = node.get("items", node) if isinstance(node, dict) else node
        except:
            current_path, active_menu = [], menu_data

        rofi_list, options_dict = [], {}
        path_str = " > ".join(current_path)

        # 5. Build Rofi List
        if not current_path:
            # A. User Categories
            cats = sorted(menu_data.keys(), key=lambda x: weights.get(f"HOME:{x}", 0), reverse=True)
            for cat in cats:
                val = menu_data[cat]
                icon = val.get("icon", FOLDER_ICON) if isinstance(val, dict) else FOLDER_ICON
                label = f"{icon}  {cat}"
                rofi_list.append(f"{label}")
                options_dict[label] = cat
            
            # B. Pinned Modes
            for m_key in ["run", "apps", "config", "opts"]:
                label = LABELS[m_key]
                rofi_list.append(f"{label}")
                options_dict[label] = label

            rofi_list.append(SEP_LINE)

            # C. Home Search Pool
            run_pool = {f"{k.split('RUN:')[1]}    ({LABELS['run']})": k.split('RUN:')[1] for k in weights.keys() if k.startswith("RUN:")}
            flat_menu = engine.get_flat_menu(menu_data)
            combined_pool = {**flat_menu, **run_pool}
            
            def global_sort(x):
                clean_name = x.split("\0")[0]
                if clean_name.endswith(f"({LABELS['apps']})"): return weights.get(f"APPS:{clean_name.split('    (')[0]}", 0)
                if clean_name.endswith(f"({LABELS['run']})"): return weights.get(f"RUN:{clean_name.split('    (')[0]}", 0)
                return weights.get(f"HOME:{clean_name}", 0)
            
            sorted_pool = sorted(combined_pool.keys(), key=global_sort, reverse=True)
            rofi_list.extend(sorted_pool)
            for k in combined_pool.keys(): 
                options_dict[k.split("\0")[0]] = k.split("\0")[0] 

            # D. Internal Menu
            for label in INTERNAL_MENU.keys():
                rofi_list.append(f"{label}")
                options_dict[label] = label
        else:
            # Sub-menu navigation
            print(is_direct_mode, path_depth, current_path)
            if (not is_direct_mode) and path_depth >= 1:
                rofi_list.append(f"{LABELS['back']}")
            if path_depth >= 2:
                rofi_list.append(f"{LABELS['home']}")
            
            items = list(active_menu.keys())
            if in_apps:
                items.sort(key=lambda x: (weights.get(f"APPS:{x}", 0), x.lower()), reverse=True)
                
                for i in items: rofi_list.append(f"{i}\0icon\x1f{active_menu[i].get('icon', '')}")
            elif in_run:
                items.sort(key=lambda x: (weights.get(f"RUN:{x}", 0), x.lower()), reverse=True)
                for i in items: rofi_list.append(f"🚀  {i}")
            elif in_config:
                home = os.path.expanduser("~")
                def config_sort(x):
                    return (weights.get(f"CONFIG:{x}", 0), os.path.basename(x).lower())
                
                items.sort(key=config_sort, reverse=True)
                for fp in items:
                    fname = os.path.basename(fp)
                    label = f"📄 {fname}    ({fp.replace(home, '~')})"
                    w = weights.get(f"CONFIG:{fname}", 0)
                    icon = "🔥" if w > 5 else "📄"
                    rofi_list.append(f"{label}")
                    options_dict[label] = fp
            else:
                items.sort(key=lambda x: weights.get(f"{path_str}:{x}", 0), reverse=True)
                for i in items:
                    v = active_menu[i]
                    icon = v.get("icon", FOLDER_ICON) if isinstance(v, dict) else FOLDER_ICON
                    label = f"{icon}  {i}"
                    rofi_list.append(f"{label}")
                    options_dict[label] = i

        # 6. Interaction
        p_key = "HUB" if not current_path else current_path[0]
        symbol = PROMPT_ICONS.get(p_key, PROMPT_ICONS["DEFAULT"])
        breadcrumb = symbol if not current_path else f"{path_str}"
        
        proc = subprocess.run([str(x) for x in rofi_base_cmd] + ["-p", breadcrumb], input="\n".join(rofi_list), text=True, capture_output=True)
        choice = proc.stdout.strip().split("\0")[0]
        if not choice or choice == SEP_LINE:
            if not choice: sys.exit(0)
            continue

        # 7. Execution Engine
        if choice.startswith(LABELS["back"]):
            if current_path: current_path.pop()
        elif choice.startswith(LABELS.get("home", "🏠")) and LABELS.get("home") in choice:
            current_path = []
        elif choice in LABELS.values():
            current_path = [choice]
        else:
            # Web Search
            parts = choice.split()
            if len(parts) > 1 and parts[0] in SEARCH_PROVIDERS:
                subprocess.Popen(f"xdg-open '{SEARCH_PROVIDERS[parts[0]]}{'+'.join(parts[1:])}'", shell=True)
                sys.exit(0)

            f_key = options_dict.get(choice, choice)
            
            # Resolve Selection
            if not current_path:
                sel = INTERNAL_MENU.get(f_key) or combined_pool.get(f_key) or menu_data.get(f_key)
            else:
                sel = active_menu.get(f_key)
            
            if sel is None and in_run: sel = choice.replace("🚀  ", "")
            if sel is None: continue

            if isinstance(sel, dict) and ("items" in sel or "cmd" not in sel):
                current_path.append(f_key)
            else:
                cmd = str(sel.get("cmd", sel) if isinstance(sel, dict) else sel)
                
                if cmd == "INTERNAL:HELP":
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt') as t:
                        t.write(get_internal_help()); t.flush()
                        subprocess.run(["yad", "--text-info", f"--filename={t.name}", "--title=Help", "--width=600", "--height=500", "--center", "--fontname=Monospace 11"])
                    continue
                if cmd == "INTERNAL:CLEAR_HIST":
                    state["history"] = {}; config.save_json(config.STATE_PATH, state); sys.exit(0)

                # History
                is_r = "(" + LABELS["run"] in choice or in_run
                if settings.get("remember_history", True):
                    if is_r: w_key = f"RUN:{cmd[5:] if cmd.startswith('TERM:') else cmd}"
                    elif in_apps: w_key = f"APPS:{f_key}"
                    else: w_key = f"{path_str if current_path else 'HOME'}:{f_key}"
                    weights[w_key] = weights.get(w_key, 0) + 1
                
                state["last_path"], state["history"] = current_path, weights
                config.save_json(config.STATE_PATH, state)

                # Launch
                term = settings.get("terminal_emulator", "wezterm start --")
                if cmd.startswith("EDT:"):
                    f_cmd = f"{term} {settings.get('editor', 'nvim')} '{os.path.expanduser(cmd[4:].strip())}'"
                elif cmd.startswith("WEB:"):
                    f_cmd = f"xdg-open '{cmd[4:] if '://' in cmd[4:] else 'https://' + cmd[4:]}'"
                elif (os.path.basename(cmd.split()[0]) if cmd.split() else "") in CLI_ONLY or cmd.startswith("TERM:"):
                    payload = cmd[5:] if cmd.startswith("TERM:") else cmd
                    f_cmd = f"{term} bash -c '{payload}; echo; read'"
                else: 
                    f_cmd = cmd

                subprocess.Popen(f_cmd, shell=True, start_new_session=True)
                sys.exit(0)

        state["last_path"] = current_path
        config.save_json(config.STATE_PATH, state)

if __name__ == "__main__":
    main()