from flask import request, Blueprint, jsonify

from .dbHelper import getSqlConnection
from .utils import checkUser

library = Blueprint("library", __name__)


@library.route("", methods=["GET"])
def getLibrariesF():
    checkUser("admin")
    return jsonify(
        {"status": "ok", "data": getLibraries(request.args.get("mediatype"))}
    )


def getLibraries(mediaType=None):
    sqlConnection, cursor = getSqlConnection()
    if mediaType is not None:
        cursor.execute(
            "SELECT id, name, path, mediaType FROM libraries WHERE mediaType = %(mediatype)s;",
            {"mediatype": mediaType},
        )
    else:
        cursor.execute(
            "SELECT id, name, path, mediaType FROM libraries;",
        )
    data = cursor.fetchall()
    sqlConnection.close()
    return data


def checkLibraryType(idLib, mediaType) -> bool:
    lib = getLibrary(idLib)
    if lib is None:
        return False
    return int(lib["mediaType"]) == int(mediaType)


@library.route("<int:idLib>", methods=["GET"])
def getLibraryF(idLib: int):
    checkUser("admin")
    return jsonify({"status": "ok", "data": getLibrary(idLib)})


def getLibrary(idLib: int):
    sqlConnection, cursor = getSqlConnection()
    cursor.execute(
        "SELECT id, name, path, mediaType FROM libraries WHERE id = %(idLib)s;",
        {"idLib": idLib},
    )
    data = cursor.fetchone()
    sqlConnection.close()
    return data