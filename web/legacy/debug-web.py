from conceptnet5.api import app
if __name__ == '__main__':
    app.debug = True
    app.run('0.0.0.0', debug=True, port=10052)
