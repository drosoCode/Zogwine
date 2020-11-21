from mysql.connector.pooling import MySQLConnectionPool
import redis
import json
from .log import logger

with open("config/config.json") as f:
    configData = json.load(f)
    logger.info("Configuration loaded")

_sqlPool = MySQLConnectionPool(
    pool_name="zogwine",
    pool_reset_session=False,
    **configData["db"],
    use_unicode=True,
    charset="utf8",
    pool_size=10
)

r_userTokens = redis.Redis(
    host=configData["redis"]["host"],
    port=configData["redis"]["port"],
    db=configData["redis"]["usersDB"],
)
r_runningThreads = redis.Redis(
    host=configData["redis"]["host"],
    port=configData["redis"]["port"],
    db=configData["redis"]["threadsDB"],
)
r_userFiles = redis.Redis(
    host=configData["redis"]["host"],
    port=configData["redis"]["port"],
    db=configData["redis"]["filesDB"],
)


def getSqlConnection(with_cursor=True):
    sqlConnection = _sqlPool.get_connection()
    sqlConnection.connect()
    if not with_cursor:
        return sqlConnection
    cursor = sqlConnection.cursor(dictionary=True, buffered=True)
    return (sqlConnection, cursor)
