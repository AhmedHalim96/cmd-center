import subprocess

def build_rofi_args(settings):
    loc_val = {"top": 2, "bottom": 7, "left": 4, "right": 5, "center": 0}.get(settings.get("location", "center"), 0)
    width, lines = settings.get("width", 30), settings.get("height", 12)
    
    # We hardcode columns: 1 here to ensure a vertical list layout
    theme = (
        f"window {{ width: {width}%; location: {settings.get('location', 'center')}; }} "
        f"listview {{ lines: {lines}; columns: 1; }}"
    )
    
    return ["rofi", "-dmenu", "-i", "-show-icons", "-location", str(loc_val), "-theme-str", theme]

def get_flat_menu(menu, prefix=""):
    flat = {}
    for key, value in menu.items():
        if isinstance(value, dict) and "cmd" not in value:
            new_prefix = f"{prefix} > {key}" if prefix else key
            flat.update(get_flat_menu(value, new_prefix))
        else:
            display_key = f"{key}    ({prefix})" if prefix else key
            flat[display_key] = value
    return flat