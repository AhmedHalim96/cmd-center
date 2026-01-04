import os, json, sys

BASE_DIR = os.path.expanduser("~/.config/cmd-center")
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
STATE_PATH = os.path.join(BASE_DIR, "state.json")

def load_json(path):
    if os.path.exists(path):
        try:
            with open(path, 'r') as f: return json.load(f)
        except: return {}
    return {}

def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f: json.dump(data, f, indent=2)

def get_colors():
    return {
        "blue": "\033[94m", "green": "\033[92m", 
        "yellow": "\033[93m", "reset": "\033[0m", "bold": "\033[1m"
    }