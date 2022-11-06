from flask import Blueprint, render_template, jsonify, request
from common import ya_h3_zoom

h3grid = Blueprint('h3grid', __name__, template_folder='templates', static_folder='static')



import json
import os
from flask import Flask, send_file, jsonify, make_response, request, current_app, Response, render_template

import uuid
import optHexesFunc



ENVIRONMENT = os.environ


def getGeoJSON(coords):
    coords = list(map(lambda x: float(x), coords))

    lu_p_arr = [coords[0], coords[1]]
    ru_p_arr = [coords[2], coords[1]]
    rb_p_arr = [coords[2], coords[3]]
    lb_p_arr = [coords[0], coords[3]]
    coordinates = [
        [
            lu_p_arr,
            ru_p_arr,
            rb_p_arr,
            lb_p_arr,
            lu_p_arr
        ]
    ]

    geoJson = {
        "type": "Polygon",
        "coordinates": coordinates
    }
    return geoJson


def getAntiGeoJSON(coords):
    coords = list(map(lambda x: float(x), coords))

    lu_p_arr = f'{coords[1]} {coords[0]}'
    ru_p_arr = f'{coords[1]} {coords[2]}'
    rb_p_arr = f'{coords[3]} {coords[2]}'
    lb_p_arr = f'{coords[3]} {coords[0]}'
    getAntiGeoJSON = ",".join(
        [
            lu_p_arr,
            ru_p_arr,
            rb_p_arr,
            lb_p_arr,
            lu_p_arr
        ])
    return getAntiGeoJSON

def prodRespFromFeatures(features, callback_id):
    fc2 = {
        "type": "FeatureCollection",
        "features": features
    }
    ret = f'{callback_id}(' + json.dumps(fc2) + ')'
    response = Response(ret, mimetype='text/xml')
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Methods', 'GET, PUT, POST, DELETE, OPTIONS')
    response.headers.add('Access-Control-Max-Age', '1000')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With')
    response.headers.add('Content-type', 'text/xml')
    return response



def produce_hexes(resp_string, request):
    callback_id = request.args.get('callback')
    string_arr = resp_string.split('/')
    ya_zoom = string_arr[-1]
    coords = string_arr[-2].split(',')
    geoJson = getGeoJSON(coords=coords)

    polylines = optHexesFunc.create_hexagons(geoJson, h3_zooms=ya_h3_zoom[ya_zoom])
    features = []

    for polyline in polylines:
        features.append({
            "type": "Feature",
            "id": str(uuid.uuid4()),
            "geometry": {
                "coordinates": polyline,
                "type": "LineString"
            },
            "properties": {
                "hintContent": f'',
            },
            "options": {
                "zIndex": 1,

                "strokeWidth": 2,
                "strokeColor": "aaaaff",
                "strokeOpacity": 1
            }
        })
    return prodRespFromFeatures(features, callback_id)


@h3grid.route('/api/v1/hexes/<path:resp_string>')
def returnh3grid(resp_string):
    return produce_hexes(resp_string=resp_string, request=request)



@h3grid.route('/')
def index():
    return render_template('h3grid/index.html')

