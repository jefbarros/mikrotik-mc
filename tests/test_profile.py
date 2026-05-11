from copy import deepcopy
from pathlib import Path

import pytest
import yaml

from src.exceptions import ProfileError
from src.profile import load_profile


EXAMPLE = Path("profiles/example.branch-reset.yaml")


def write_profile(tmp_path, data):
    path = tmp_path / "profile.yaml"
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return path


def load_example_data():
    return yaml.safe_load(EXAMPLE.read_text(encoding="utf-8"))


def test_valid_profile_passes():
    profile = load_profile(EXAMPLE)
    assert profile.router_identity == "RB-RESETADA"


def test_invalid_lan_fails(tmp_path):
    data = load_example_data()
    data["interfaces"]["lan_bridge"]["address"] = "not-a-cidr"
    with pytest.raises(ProfileError):
        load_profile(write_profile(tmp_path, data))


def test_ssh_open_to_world_fails(tmp_path):
    data = load_example_data()
    data["management"]["allow_ssh_from"] = ["0.0.0.0/0"]
    with pytest.raises(ProfileError):
        load_profile(write_profile(tmp_path, data))


def test_profile_without_management_source_fails(tmp_path):
    data = load_example_data()
    data["management"]["allow_ssh_from"] = []
    data["management"]["allow_winbox_from"] = []
    with pytest.raises(ProfileError):
        load_profile(write_profile(tmp_path, data))


def test_wan_and_lan_same_interface_fails(tmp_path):
    data = load_example_data()
    data["interfaces"]["lan_bridge"]["ports"] = ["ether1"]
    with pytest.raises(ProfileError):
        load_profile(write_profile(tmp_path, data))


def test_admin_cannot_be_automation_user(tmp_path):
    data = load_example_data()
    data["management"]["automation_user"] = "admin"
    with pytest.raises(ProfileError):
        load_profile(write_profile(tmp_path, data))

