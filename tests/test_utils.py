#  Copyright (c) 2026 by Lukas Behammer
#  University of Augsburg
#  Department of Computer Science
#  Chair of Informatics for Medical Technology
#
#  SPDX-License-Identifier: BSD-3-Clause

from dataclasses import dataclass
from enum import Enum

from pytermite.connection import WirelessConnection, WiredConnection

from pytermite import utils



class Color(Enum):
    RED = 1
    GREEN = 2


@dataclass
class Thing:
    a: int
    b: str


def test_create_base_url_short_serial():
    url = utils.create_ip_address("C123456789")
    assert url == "172.27.189.51"


def test_reverse_and_serialize_dict_dataclass_and_enum():
    d = {"cam1": "SER1", "cam2": "SER2"}
    rev = utils.reverse_dict(d)
    assert rev["SER1"] == "cam1"

    thing = Thing(1, "x")
    data = {"t": thing, "c": Color.RED, "n": None, "s": "ok", "i": 3}
    serialized = utils.serialize_dict(data)
    assert serialized["t"]["a"] == 1
    assert serialized["t"]["b"] == "x"
    assert serialized["c"] == "RED"
    assert serialized["n"] is None


def test_load_serial_numbers_from_json_and_write(tmp_path):
    p = tmp_path / "serials.json"
    mapping = {"camA": "S1", "camB": "S2"}
    utils.write_json_to_file(mapping, p)
    loaded = utils.load_serial_numbers_from_json(p)
    assert loaded == mapping

    # write with no .json suffix
    p2 = tmp_path / "out"
    utils.write_json_to_file(mapping, p2)
    assert p2.with_suffix(".json").exists()


def test_serialize_fallback_object():
    class X:
        def __init__(self):
            self.foo = "bar"

    x = X()
    out = utils.serialize_dict({"x": x})
    assert out["x"]["foo"] == "bar"

def test_serializable_connections():
    for connection_type in [WirelessConnection, WiredConnection]:
        connection = object.__new__(connection_type)

        connection._wired_api = object()
        connection.streaming = object()
        connection._loop = object()
        connection.target = "Test1"

        connections = {connection}

        connections_serializable = utils.serializable_connections(connections)

        original = next(iter(connections))
        serializable = next(iter(connections_serializable))

        assert serializable is not original

        for name, value in vars(original).items():
            value_serializable = getattr(serializable, name)

            if name in {"_wired_api", "streaming", "_loop"}:
                assert value_serializable is None
            else:
                assert value_serializable == value

def test_parse_settings_and_status():
    v1, v2 = utils.parse_setting("test", "test", mode="test")
    assert v1 is None and v2 is None

    v1, v2 = utils.parse_setting("test", "test")
    assert v1 is None and v2 is None

    settings = utils._load_bundled_json("OpenGoPro_Settings.json")

    v1, v2 = utils.parse_setting("2", "test")
    assert v1 is None and v2 is None

    for setting in settings:
        for option, value in settings[setting]["options"].items():
            sname, oname = utils.parse_setting(setting, option, mode="name")
            assert sname == settings[setting]["name"] and\
                oname == settings[setting]["options"][option]

            sid, oid = utils.parse_setting(sname, oname)
            assert sname == settings[sid]["name"] and\
                oname == settings[sid]["options"][oid]

    statuses = utils._load_bundled_json("OpenGoPro_Statuses.json")
    for status in statuses:
        status_name = utils.parse_status(status)
        assert status_name == statuses[status]