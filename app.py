# -*- coding: utf-8 -*-
from flask import Flask, render_template, jsonify, send_from_directory, request
from flask import Flask, request, jsonify, make_response
import os

app = Flask(__name__)
from flask_cors import CORS
app = Flask(__name__)
CORS(app)


from h3grid.h3grid import h3grid
from games1.games1 import games1
from arrangeKali.arrangeKali import arrangeKali

app.register_blueprint(h3grid, url_prefix='/h3grid')
app.register_blueprint(games1, url_prefix='/games1')
app.register_blueprint(arrangeKali, url_prefix='/arrangeKali')


def _build_cors_preflight_response():
    response = make_response()
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add('Access-Control-Allow-Headers', "*")
    response.headers.add('Access-Control-Allow-Methods', "*")
    return response

def _corsify_actual_response(response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response



@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


@app.route('/')
def index():
    return render_template('index.html')



port = 5000
if __name__ == '__main__':
    app.run(debug=False, port=port, use_reloader=False,threaded=True, host='0.0.0.0')

# if __name__ == '__main__':
#     from waitress import serve
#     print (f'http://{socket.gethostname()}:8001')
#     serve(app, listen=f'*:{port}')
