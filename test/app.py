#!/usr/bin/env python3
import rss
import os
from bottle import route, run, template

@route('/')
def index():
    seasons = rss.fetchSeasons('dagsnytt')
    return str(rss.generateFeed(seasons))

@route('/show/<name>')
def fetchSeason(name):
    seasons = rss.fetchSeasons(name)
    return rss.generateFeed(seasons)

@route('/recode/<name>/<id>')
def recode(name, id):
    seasons = rss.fetchSeasons(name)
    season = seasons.pop()
    episode = [e for e in season['episodes'] if e['id'] == id][0]

    return str(rss.getAssetsAsMp3(rss.getBestQualityAssets(episode['assets'])))


run(host=os.getenv('HOST', 'localhost'), port=os.getenv('PORT', 8080))

