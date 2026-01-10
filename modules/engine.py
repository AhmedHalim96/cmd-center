def build_rofi_args(settings, enable_icons=False):
    """
    Constructs the Rofi command. Icons are enabled only if 
    enable_icons is True or the global setting is True.
    """
    loc_val = {"top": 2, "bottom": 7, "left": 4, "right": 5, "center": 0}.get(settings.get("location", "center"), 0)
    width, lines = settings.get("width", 30), settings.get("height", 12)
    
    theme = (
        f"window {{ width: {width}%; location: {settings.get('location', 'center')}; }} "
        f"listview {{ lines: {lines}; columns: 1; }}"
    )
    
    cmd = ["rofi", "-dmenu", "-i", "-location", str(loc_val), "-theme-str", theme]
    
    # Toggle icons based on the passed state
    if enable_icons or settings.get("show_icons_globally", False):
        cmd.append("-show-icons")
        
    return cmd

def get_flat_menu(menu, prefix="", in_apps=False):
    """
    Recursively flattens the menu for Global Search.
    Supports both old (string) and new (object) configurations.
    """
    flat = {}
    
    for key, val in menu.items():
        # 1. Resolve the Display Label (Check for 'label' key, fallback to JSON key)
        label = val.get("label", key) if isinstance(val, dict) else key
        
        # 2. Identify if this is a Category (Folder)
        # It's a folder if it has an 'items' key OR if it's a dict WITHOUT a 'cmd' key
        is_folder = isinstance(val, dict) and ("items" in val or "cmd" not in val)
        
        if is_folder:
            # Dive deeper into the folder
            # If the folder uses the new structure, we pass 'items', else pass the dict itself
            sub_menu = val.get("items", val)
            new_prefix = f"{prefix} > {label}" if prefix else label
            flat.update(get_flat_menu(sub_menu, new_prefix))
        else:
            # 3. This is a Command (Leaf)
            # Add icon metadata if available in the new format
            icon = val.get("icon", "system-run") if isinstance(val, dict) else "system-run"
            
            display_name = f"{label}    ({prefix})" if prefix else label
            # We use Rofi's metadata protocol: \0icon\x1fPATH
            rofi_entry = f"{display_name}"
            
            flat[rofi_entry] = val
            
    return flat