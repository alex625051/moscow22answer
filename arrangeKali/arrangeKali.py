# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, jsonify, request, redirect
from common import ya_h3_zoom, getJson
import time
import common
import hashlib
from random import randrange
import psycopg2
import pandas as pd

arrangeKali = Blueprint('arrangeKali', __name__, template_folder='templates', static_folder='static')

import json
import os
from flask import Flask, send_file, jsonify, make_response, request, current_app, Response, render_template

import uuid
import optHexesFunc

ENVIRONMENT = os.environ
POSTGRESuser = common.POSTGRESuser
POSTGRESpassword = common.POSTGRESpassword
POSTGREShost = common.POSTGREShost
POSTGRESport = common.POSTGRESport
POSTGRESdatabase = common.POSTGRESdatabase


def getConnection():
    connection = psycopg2.connect(user=POSTGRESuser,
                                  # пароль, который указали при установке PostgreSQL
                                  password=POSTGRESpassword,
                                  host=POSTGREShost,
                                  port=POSTGRESport,
                                  database=POSTGRESdatabase)
    return connection


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


def produceFutureCollection(features, arrangeId=""):
    fc2 = {
        "type": "FeatureCollection",
        "features": features
    }
    ret = {"success": True, "data": fc2, "error": f"", "arrangeId": arrangeId}
    ret = f'' + json.dumps(ret)
    response = Response(ret)

    return response

def getCategory(row, pp):
    if row.get('category'): return row['category']
    if pp=="nestacitorg": return "Нестационарные торговые точки"
    if pp=="nestacipechat": return "Нестационарные киоски печати"
    if pp=="mfc": return "Многофункциональные центры"

def getCommonname(row, pp):
    if row.get('commonname'): return row['commonname']

    if pp=="nestacitorg": return "Киоск"
    if pp=="nestacipechat": return "Киоск"
    if pp=="mfc": return "МФЦ"

def getAdmission(paramsRecieved, connection):
    targetPoints = paramsRecieved.get('targetPoints', "mfc,biblioteks,domacultury,nestacipechat,nestacitorg,sportivnuch") or "mfc,biblioteks,domacultury,nestacipechat,nestacitorg,sportivnuch"
    targetArea = paramsRecieved.get('targetArea')
    targetDistrict = paramsRecieved.get('targetDistrict')
    targetDoorstep = paramsRecieved.get('targetDoorstep')
    targetCoverage = paramsRecieved.get('targetCoverage')
    targetPostsNumber = paramsRecieved.get('targetPostsNumber')
    if not targetPoints: targetPoints="mfc,biblioteks,domacultury,nestacipechat,nestacitorg,sportivnuch"
    print(targetPoints)
    if not targetDistrict:
        targetDistrict_query = ''
    else:
        targetDistrict_query = f"""AND name in ({",".join([f"'{dis}'" for dis in targetDistrict.split(",")])})"""

    data = pd.DataFrame([])
    for pp in list(targetPoints.split(",")):
        sql = f"""
                SELECT *
              FROM ratequadro_{pp}buildings INNER JOIN (SELECT * from mo
                  WHERE true
                    {targetDistrict_query}
                  ) as moF
              ON ST_covers(moF.areamulty,ratequadro_{pp}buildings.point  )
            order by flatsvolume DESC;

        """
        oneDF = pd.read_sql_query(sql, connection)
        oneDF['category'] = oneDF.apply(lambda x: getCategory(x,pp), axis=1)
        oneDF['commonname'] = oneDF.apply(lambda x: getCommonname(x,pp), axis=1)
        oneDF=oneDF[['category', 'commonname', 'lat','lon','trafficrate','flatsvolume','buildingids']].copy()
        data = pd.DataFrame(oneDF.to_dict('records')+data.to_dict('records'))

    data.drop('buildingids',axis=1,inplace=True)
    if targetPostsNumber:
        try:
            targetPostsNumber=int(targetPostsNumber)
            if len(data)>targetPostsNumber:
                data=data[0:targetPostsNumber:].copy()
        except:
            pass
    return data.to_dict('records')


def make_take_order(paramsRecieved):
    connection = getConnection()
    sha = hashlib.sha1(str(paramsRecieved).encode())
    arrangeId = sha.hexdigest()
    sortedOrdersColumns = list(sorted(list(paramsRecieved.keys())))
    sortedAnswerColumns = list(sorted(list(common.answerStructure.keys())))
    cursor = connection.cursor()
    columnsAnswersTypeString = ",".join([f'{key} TEXT' for key in sortedAnswerColumns] + ['arrangeId TEXT'])
    columnsOrdersTypeString = ",".join(
        [f'{key} TEXT' for key in sortedOrdersColumns] + ['arrangeId TEXT', 'status TEXT'])
    columnsOrdersForWrite = ",".join([f'{key}' for key in sortedOrdersColumns] + ['arrangeId', 'status'])

    cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS orders(
                        id SERIAL PRIMARY KEY, {columnsOrdersTypeString});   
    CREATE TABLE IF NOT EXISTS answers(
                        id SERIAL PRIMARY KEY, {columnsAnswersTypeString});                             
    SELECT * FROM orders 
            WHERE arrangeId like '{arrangeId}'                                 
                    """)
    order = cursor.fetchone()
    if not order:
        valuesOrdersStringNew = ",".join(
            [f"'{paramsRecieved[key]}'" for key in sortedOrdersColumns] + [f"'arrangeId'"] + ["'inProcess'"])

        cursor.execute(f"""INSERT INTO orders ({columnsOrdersForWrite}) VALUES 
          (
                 {valuesOrdersStringNew}
                )  
                    """)
    #
    connection.commit()
    dat = getAdmission(paramsRecieved, connection)

    cursor.close()
    connection.close()
    return arrangeId, dat


def produceArrangePoints(resp_string, request):
    callback_id = request.args.get('callback')
    string_arr = resp_string.split('/')
    ya_zoom = string_arr[-1]
    coords = string_arr[-2].split(',')
    arrangeId = string_arr[-3]
    geoJson = getGeoJSON(coords=coords)

    arrangeObjects = getJson('biblioteki.json')['data'].get('features', [])

    features = []
    for oneObject in arrangeObjects:  # Объект может состоять из множества точек (корпусов)
        hintContent = '<br/>'.join(
            [str(oneObject['properties']['Attributes'][k]) for k in oneObject['properties']['Attributes'].keys()])

        for oneCoords in oneObject['geometry']['coordinates']:
            features.append({
                "type": "Feature",
                "id": str(uuid.uuid4()),
                "geometry": {
                    "coordinates": list(reversed(oneCoords)),
                    "type": "Point"
                },
                "properties": {
                    "balloonContentBody": oneObject['properties']['Attributes']['CommonName'],
                    "balloonContentHeader": 'хедер',
                    "balloonContentBody": "боди",
                    "balloonContentFooter": 'футер'
                }

            })
    return prodRespFromFeatures(features, callback_id)


def produceArrangePointsCollection(resp_string, request):
    string_arr = resp_string.split('/')
    arrangeId = string_arr[-1]
    arrangeObjects = getJson('biblioteki.json')['data'].get('features', [])

    features = []

    for oneObject in arrangeObjects:  # Объект может состоять из множества точек (корпусов)
        for oneCoords in oneObject['geometry']['coordinates']:
            features.append({
                "type": "Feature",
                "id": str(uuid.uuid4()),
                "geometry": {
                    "coordinates": list(reversed(oneCoords)),
                    "type": "Point"
                },
                "properties": {
                    "hintContent": oneObject['properties']['Attributes']['CommonName'],
                    # "hintContent": '<br/>'.join([str(oneObject['properties']['Attributes'][k]) for k in oneObject['properties']['Attributes'].keys()]),
                },

            })
    return produceFutureCollection(features=features, arrangeId=arrangeId)

def produceArrangePointsCollection2(data):
    arrangeObjects = data

    features = []

    for oneObject in arrangeObjects:  # Объект может состоять из множества точек (корпусов)
        features.append({
            "type": "Feature",
            "id": str(uuid.uuid4()),
            "geometry": {
                "coordinates": f"{oneObject.get('lon')}, {oneObject.get('lat')}",
                "type": "Point"
            },
            "properties": {
                "hintContent": f"{oneObject.get('category')}. {oneObject.get('commonname')}. {oneObject.get('flatsvolume')}",
                # "hintContent": '<br/>'.join([str(oneObject['properties']['Attributes'][k]) for k in oneObject['properties']['Attributes'].keys()]),
            },

        })
    fc2 = {
        "type": "FeatureCollection",
        "features": features
    }
    return fc2




def takeTestAnswer():
    arrangeObjects = getJson('bibliotekiFull.json')['data']

    returnList = []
    for oneObject in arrangeObjects:  # Объект может состоять из множества точек (корпусов)
        returnList.append({
            "type": "Постомат",
            "point_id": str(uuid.uuid4()),
            "coordinates": oneObject['geoData']["coordinates"],
            "modelPointRate": (randrange(765, 1000)) / 1000,
            "modelName": "Kali model",
            "admArea": oneObject['ObjectAddress'][0]['AdmArea'],
            "district": oneObject['ObjectAddress'][0]['District'],
            "nearestAddress": oneObject['ObjectAddress'][0]['Address'],
            "nearestObject": oneObject['CommonName'],
            "nearestWorkingTime": ", ".join([': '.join(d.values()) for d in oneObject[
                'WorkingHours']]) + f'. {oneObject["ClarificationOfWorkingHours"]}',
            "nearestVisitors": oneObject.get('NumOfVisitors')

        })
    return returnList


def produceArrangeList(resp_string, request):
    string_arr = resp_string.split('/')
    arrangeId = string_arr[-1]
    if False:  # arrangeId not in ['test_arrange1']:
        return {"success": False, "data": [], "error": f"arrange id {arrangeId} in not exists. try test: test_arrange1"}

    returnList = takeTestAnswer()
    returnList = {"success": True, "data": returnList, "arrangeId": arrangeId}
    ret = json.dumps(returnList)
    response = Response(ret)
    return response


@arrangeKali.route('/api/v1/get_points_list/<path:resp_string>')
def returnArrangeList(resp_string):
    return produceArrangeList(resp_string=resp_string, request=request)


@arrangeKali.route('/api/v1/get_points/<path:resp_string>')
def returnArrangePoints(resp_string):
    return produceArrangePoints(resp_string=resp_string, request=request)


@arrangeKali.route('/api/v1/get_points_collection/<path:resp_string>')
def returnArrangePointsCollection(resp_string):
    return produceArrangePointsCollection(resp_string=resp_string, request=request)


def queryToDB(paramsRecieved):
    targetArea = paramsRecieved.get('targetArea')
    targetDistrict = paramsRecieved.get('targetDistrict')
    targetDoorstep = paramsRecieved.get('targetDoorstep')
    targetCoverage = paramsRecieved.get('targetCoverage')
    targetPostsNumber = paramsRecieved.get('targetPostsNumber')
    pass


@arrangeKali.route('/api/v1/postArrangeOrder/', methods=['GET', 'POST'])
def postArrangeOrder():
    paramsEtalon = {
        "targetPoints": "",
        "targetArea": "Западный",
        "targetDistrict": [
            "Филёвский Парк",
            "Внуково",
            "Можайский"
        ],
        "targetDoorstep": 100,
        "targetCoverage": 10,
        "targetPostsNumber": 50
    }

    paramsRecieved = {}
    for param in paramsEtalon:
        paramsRecieved[param] = request.args.get(param, "")
    print(paramsRecieved)
    # paramsRecieved = paramsEtalon
    # targetArea = request.args.get('targetArea')
    # targetDistrict = request.args.get('targetDistrict')
    # targetDoorstep = request.args.get('targetDoorstep')
    # targetCoverage = request.args.get('targetCoverage')
    # targetPostsNumber = request.args.get('targetPostsNumber')
    sha = hashlib.sha1(str(paramsRecieved).encode())

    # sha = hashlib.sha1(f"{targetArea},{targetDistrict},{targetDoorstep},{targetCoverage},{targetPostsNumber}".encode())
    arrangeId, data = make_take_order(paramsRecieved)

    mapData=produceArrangePointsCollection2(data)
    return {"success": True, "data": {"map":mapData, "table":data}, "arrangeId": arrangeId}


@arrangeKali.route('/api/v1/arrangeOrderStatus/<path:resp_string>', methods=['GET'])
def arrangeOrderStatus(resp_string):
    string_arr = resp_string.split('/')
    arrangeId = string_arr[-1]
    arrangeOrderStatus = ['ready', 'inProcess', 'except'][randrange(0, 3)]
    return {"success": True, "data": [], "arrangeId": arrangeId, 'arrangeOrderStatus': arrangeOrderStatus}


@arrangeKali.route('/')
def index():
    return render_template('arrangeKali/index.html')


@arrangeKali.route('/api/v1/')
def apiDoc2():
    return render_template('arrangeKali/apiDoc.html')


@arrangeKali.route('/apiDoc/')
def apiDoc():
    return render_template('arrangeKali/apiDoc.html')


@arrangeKali.route('/api/v1/get_points_list/')
def return404_1():
    return render_template('arrangeKali/apiDoc.html')


@arrangeKali.errorhandler(404)
def page_not_found(e):
    return render_template('arrangeKali/apiDoc.html'), 404
