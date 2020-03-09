from log import logger
from server import api, app

from tornado.wsgi import WSGIContainer
from tornado.ioloop import IOLoop
from tornado.web import Application

logger.info('Starting Program ...')

#api.runScan()
#app.run(host='0.0.0.0', port=8080, threaded=True)

tr = WSGIContainer(app)

application = Application([
    (r".*", WSGIContainer(app))
])

application.listen(8080, address='0.0.0.0')
IOLoop.instance().start()