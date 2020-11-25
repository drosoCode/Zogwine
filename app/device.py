import time
from flask import request, Blueprint, jsonify, abort, Response, send_file
import redis
import os
import json
from importlib import import_module
import sys

from .transcoder import transcoder
from .log import logger
from .utils import checkArgs, getFile
from .dbHelper import getSqlConnection, r_userFiles, r_userTokens, configData

device = Blueprint("device", __name__)
allowedMethods = ["GET", "POST"]

fncts = {
    "play": (),
    "pause": (),
    "stop": (),
    "seek": ("position"),
    "setVolume": ("volume"),
    "mute": (),
    "unmute": (),
    "position": (),
    "length": (),
    "volume": (),
    "status": (),
    "playingMedia": (),
}


@device.route("/api/device/supported")
def devices_supported():
    devs = []
    for i in os.listdir("app/devices/"):
        name = i[: i.rfind(".")]
        if i[i.rfind(".") + 1 :] == "py" and name != "PlayerBase":
            devs.append(name)

    return jsonify({"status": "ok", "data": devs})


@device.route("/api/device/list")
def devices_list():
    sqlConnection, cursor = getSqlConnection()
    cursor.execute("SELECT idDevice AS id, name, type, address, enabled FROM devices")
    data = cursor.fetchall()
    sqlConnection.close()
    for i in range(len(data)):
        data[i]["available"] = os.system("ping -c 1 -W 1 " + data[i]["address"]) == 0

    return jsonify({"status": "ok", "data": data})


@device.route("/api/device/functions")
def devices_functions():
    checkArgs(["idDevice"])

    sqlConnection, cursor = getSqlConnection()
    cursor.execute(
        "SELECT type FROM devices WHERE idDevice = %(idDevice)s",
        {"idDevice": request.args["idDevice"]},
    )
    data = cursor.fetchone()
    sqlConnection.close()

    dev = importDevice(data["type"])

    return jsonify({"status": "ok", "data": list(set(fncts.keys()) & set(vars(dev)))})


@device.route("/api/device/<function>")
def devices_function(function: str):
    checkArgs(["idDevice"])

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
            {"idDevice": request.args["idDevice"]},
        )
        data = cursor.fetchone()
        sqlConnection.close()

        if data["enabled"] == 0:
            return False
        dev = importDevice(data["type"])
        device = dev(
            request.args["token"],
            data["address"],
            data["port"],
            data["user"],
            data["password"],
            data["device"],
        )
        method = getattr(device, function)
        if callable(method):
            result = method(**args)
        else:
            result = method

        return jsonify({"status": "ok", "data": result})

    else:
        abort(400)


def importDevice(devType: str):
    sys.path.append("app/devices/")
    if not os.path.exists("app/devices/" + devType + ".py"):
        return None
    module = import_module(devType)
    return getattr(module, devType)
