from log import logger
from server import api, app

logger.info('Starting Program ...')

api.runScan()
app.run(host='0.0.0.0', port=8080)