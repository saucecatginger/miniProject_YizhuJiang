#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Apr 19 23:47:06 2020

@author: yizhu
"""

from flask import Flask, request, render_template, jsonify
from cassandra.cluster import Cluster

import json
import requests
import requests_cache

cluster = Cluster(contact_points=['172.17.0.2'],port=9042)
session = cluster.connect()

requests_cache.install_cache('eq_api_cache', backend='sqlite', expire_after=36000)

app = Flask(__name__)

@app.route('/')
def hello():
    name = request.args.get("name")
    return('<h1>Hello, {}, here to check some earthquake?</h1>'.format(name))

@app.route('/earthquake')
def profile():
    rows = session.execute("""Select * From useq.stats""")
    result = []
    for r in rows:
        result.append({"id":r.ID,"latitude":r.latitude})
    return jsonify(result)

@app.route('/earthquake/<id>')
def search(id):
    rows = session.execute( """Select * From useq.stats 
                           where id = '{}'""".format(id))
    for eq in rows:
        return('<h1>{} - latitude: {}, longtitude: {}</h1>'.format(id, eq.latitude, eq.longtitude))
    return('<h1>That earthquake does not exist!</h1>')

@app.route('/iceland', methods=['GET'])
def geteq():
    eq_url_template = 'https://apis.is/earthquake/is'
    my_latitude = request.args.get('lat','63.976')
    my_longitude = request.args.get('lng','-21.949')
    my_depth = request.args.get('depth','1.1')
    eq_url = eq_url_template.format(lat = my_latitude, lng = my_longitude, depth = my_depth)
    resp = requests.get(eq_url)
    
    if resp.ok:
        return jsonify(resp.json())
    else:
        print(resp.reason)

@app.route('/earthquake', methods=['POST'])
def create():
    session.execute("""INSERT INTO useq.stats (time,latitude,longitute,depth,mag,magType,id,place,type) VALUES ('{}',{},{},{},{},'{}','{}','{}','{}')""".format
                    (request.json['time'],float(request.json['latitude']),float(request.json['longitude']),float(request.json['depth']),float(request.json['mag']),request.json['magType'],request.json['id'],request.json['place'],request.json['type']))
    return jsonify({'message': 'updated:/records/{}'.format(request.json['id'])}), 201

@app.route('/earthquake', methods=['PUT'])
def update():
    session.execute("""UPDATE useq.stats SET latitude = {} WHERE id = '{}'""".format(float(request.json['latitude']),request.json['id']))
    return jsonify({'message': 'updated:/records/{}'.format(request.json['id'])}), 200

@app.route('/earthquake', methods=['DELETE'])
def delete():
    session.execute("""DELETE FROM useq.stats WHERE id = '{}'""".format(request.json['id']))
    return jsonify({'message': 'deleted:/records/{}'.format(request.json['id'])}), 200

if __name__=="__main__":
    app.run(host='0.0.0.0')