from conceptnet5.web_interface.web_interface import app
if __name__ == '__main__':
    app.debug = True
    app.run('0.0.0.0', debug=True, port=10053)
