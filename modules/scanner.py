import os, glob

def get_system_apps():
    apps = {}
    # Comprehensive list of desktop file locations
    paths = [
        "/usr/share/applications/*.desktop",
        "/usr/local/share/applications/*.desktop",
        os.path.expanduser("~/.local/share/applications/*.desktop"),
        # System-wide Flatpaks
        "/var/lib/flatpak/exports/share/applications/*.desktop",
        # User-specific Flatpaks (The path you requested)
        os.path.expanduser("~/.local/share/flatpak/exports/share/applications/*.desktop")
    ]
    
    for path_glob in paths:
        for entry in glob.glob(path_glob):
            # The desktop_id is used by gtk-launch to trigger the app correctly
            d_id = os.path.basename(entry)
            try:
                with open(entry, 'r') as f:
                    name, icon = None, "system-run"
                    for line in f:
                        if line.startswith("Name="): 
                            name = line.split("=")[1].strip()
                        elif line.startswith("Icon="): 
                            icon = line.split("=")[1].strip()
                        # Optimization: stop reading if we have both
                        if name and icon != "system-run":
                            break
                    
                    if name: 
                        # We use the filename (desktop_id) for gtk-launch
                        # as it's more reliable for Flatpaks than parsing Exec=
                        apps[name] = {"cmd": f"gtk-launch {d_id}", "icon": icon}
            except Exception:
                continue
    return apps

def get_binaries():
    bins = set()
    for path in os.environ.get("PATH", "").split(os.pathsep):
        if os.path.isdir(path):
            try:
                for entry in os.scandir(path):
                    if entry.is_file() and os.access(entry.path, os.X_OK):
                        bins.add(entry.name)
            except Exception:
                continue
    return sorted(list(bins))