from server import api, app
from log import logger

logger.info('Starting Program ...')

#api.runScan()
app.run(host='0.0.0.0', port=8080)