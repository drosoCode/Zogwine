from flask import request, Blueprint, jsonify

from .dbHelper import getSqlConnection
from .utils import checkUser

library = Blueprint("library", __name__)


@library.route("", methods=["GET"])
def getLibraries():
    checkUser("admin")
    sqlConnection, cursor = getSqlConnection()
    if "mediatype" in request.args:
        cursor.execute(
            "SELECT id, name, path, mediaType FROM libraries WHERE mediaType = %(mediatype)s;",
            {"mediatype": request.args["mediatype"]},
        )
    else:
        cursor.execute(
            "SELECT id, name, path, mediaType FROM libraries;",
        )
    data = cursor.fetchall()
    sqlConnection.close()
    return jsonify({"status": "ok", "data": data})


@library.route("<int:idLib>", methods=["GET"])
def getLibrary(idLib: int):
    checkUser("admin")
    sqlConnection, cursor = getSqlConnection()
    cursor.execute(
        "SELECT id, name, path, mediaType FROM libraries WHERE id = %(idLib)s;",
        {"idLib": idLib},
    )
    data = cursor.fetchone()
    sqlConnection.close()
    return jsonify({"status": "ok", "data": data})
