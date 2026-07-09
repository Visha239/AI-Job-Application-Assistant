import json
from pathlib import Path


def load_roles():
    path = Path("config/roles.json")

    with open(path, "r") as file:
        return json.load(file)


def get_role_names():
    roles = load_roles()
    return list(roles.keys())


def get_role_config(role_name):
    roles = load_roles()
    return roles.get(role_name)