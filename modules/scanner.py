import os, glob

def get_system_apps():
    apps = {}
    paths = ["/usr/share/applications/*.desktop", 
             os.path.expanduser("~/.local/share/applications/*.desktop"),
             "/var/lib/flatpak/exports/share/applications/*.desktop"]
    for path_glob in paths:
        for entry in glob.glob(path_glob):
            d_id = os.path.basename(entry)
            try:
                with open(entry, 'r') as f:
                    name, icon = None, "system-run"
                    for line in f:
                        if line.startswith("Name="): name = line.split("=")[1].strip()
                        elif line.startswith("Icon="): icon = line.split("=")[1].strip()
                    if name: apps[name] = {"cmd": f"gtk-launch {d_id}", "icon": icon}
            except: continue
    return apps

def get_binaries():
    bins = set()
    for path in os.environ.get("PATH", "").split(os.pathsep):
        if os.path.isdir(path):
            try:
                for entry in os.scandir(path):
                    if entry.is_file() and os.access(entry.path, os.X_OK):
                        bins.add(entry.name)
            except: continue
    return sorted(list(bins))