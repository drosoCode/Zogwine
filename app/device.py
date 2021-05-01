import time
from flask import request, Blueprint, jsonify, abort, Response, send_file
import redis
import os
import json
from importlib import import_module

from .transcoder import transcoder
from .log import logger
from .utils import checkArgs, getUID, generateToken, checkUser
from .dbHelper import getSqlConnection, r_userFiles, configData
from .devices.PlayerBase import PlayerBase

device = Blueprint("device", __name__)

fncts = {
    "play": [],
    "pause": [],
    "stop": [],
    "seek": ["value"],
    "setVolume": ["value"],
    "mute": [],
    "unmute": [],
    "position": [],
    "loaded": [],
    "volume": [],
    "status": [],
    "playingMedia": [],
}


def checkRights(idDevice):
    if checkUser("cast", False) or (idDevice == 1 and checkUser("receive", False)):
        return True
    else:
        abort(404)


@device.route("supported")
def devices_supported():
    checkUser("cast")
    devs = []
    for i in os.listdir("app/devices/"):
        name = i[: i.rfind(".")]
        if i[i.rfind(".") + 1 :] == "py" and name != "PlayerBase":
            devs.append(name)

    return jsonify({"status": "ok", "data": devs})


@device.route("")
def devices_list():
    checkUser("cast")
    sqlConnection, cursor = getSqlConnection()
    cursor.execute(
        "SELECT idDevice AS id, name, type, address, port, device, user, password, enabled FROM devices"
    )
    data = cursor.fetchall()
    sqlConnection.close()
    for i in range(len(data)):
        d = initDevice(data[i], True)
        data[i]["available"] = d.available
        del d, data[i]["user"], data[i]["password"], data[i]["device"]

    return jsonify({"status": "ok", "data": data})


@device.route("<int:idDevice>")
def device_data(idDevice: int):
    checkRights(idDevice)
    sqlConnection, cursor = getSqlConnection()
    cursor.execute(
        "SELECT idDevice AS id, name, type, address, port, device, user, password, enabled FROM devices WHERE idDevice = %(idDevice)s",
        {"idDevice": idDevice},
    )
    data = cursor.fetchone()
    sqlConnection.close()
    d = initDevice(data, True)
    data["available"] = d.available
    del d, data["user"], data["password"], data["device"]

    return jsonify({"status": "ok", "data": data})


@device.route("<int:idDevice>/function")
def devices_functions(idDevice: int):
    checkRights(idDevice)
    sqlConnection, cursor = getSqlConnection()
    cursor.execute(
        "SELECT type FROM devices WHERE idDevice = %(idDevice)s",
        {"idDevice": idDevice},
    )
    data = cursor.fetchone()
    sqlConnection.close()

    dev = importDevice(data["type"])

    return jsonify({"status": "ok", "data": list(set(fncts.keys()) & set(vars(dev)))})


@device.route("<int:idDevice>/function/<function>")
def devices_function(idDevice: int, function: str):
    checkRights(idDevice)
    if function in fncts.keys():
        args = {}
        for param in fncts[function]:
            if param not in request.args:
                abort(400)
            else:
                args[param] = request.args[param]

        sqlConnection, cursor = getSqlConnection()
        cursor.execute(
            "SELECT * FROM devices WHERE idDevice = %(idDevice)s",
            {"idDevice": idDevice},
        )
        data = cursor.fetchone()
        sqlConnection.close()

        if data["enabled"] == 0:
            return False
        device = initDevice(data)
        method = getattr(device, function)
        if callable(method):
            result = method(**args)
        else:
            result = method
        del device

        return jsonify({"status": "ok", "data": result})

    else:
        abort(400)


def initDevice(data, skipInit=False) -> PlayerBase:
    dev = importDevice(data["type"])
    return dev(
        getUID(),
        request.args.get("token") or generateToken(getUID()),
        data.get("address"),
        data.get("port"),
        data.get("user"),
        data.get("password"),
        data.get("device"),
        skipInit,
    )


def importDevice(devType: str):
    if not os.path.exists("app/devices/" + devType + ".py"):
        return None
    module = import_module("app.devices." + devType)
    return getattr(module, devType)
