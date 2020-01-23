from server import app, api

api.runScan()
app.run(host='0.0.0.0')