#!/usr/bin/env python3
import json, re
import sys
import m3u8
import tempfile
import urllib
from urllib.parse import urljoin
from os import getenv
from os import path
from datetime import datetime
from pydub import AudioSegment
from PyRSS2Gen import RSS2, RSSItem, Guid

appUrl = getenv('APP_URL', "http://{}:{}".format(getenv('HOST', 'localhost'), getenv('PORT', '8080')))

def fetchSeasons(name):
    seasons = []

    url = 'https://radio.nrk.no/psapi/series/%s' % ( name )
    with urllib.request.urlopen(url) as response:
        p = response.read()
        
        playlist = json.loads(p)

        print("{}, {}".format(playlist['title'], playlist['description']))
        season = {
            'name': playlist['title'],
            'description': playlist['description'],
            'episodes': []
        }

        for s in playlist['seasons']:
            if s['hasOnDemandRightsEpisodes']:
                print("{}: {} ({})".format(s['id'], s['name'], url))

                episodes = fetchEpisodes(s['id'])
                season['episodes'] = episodes
                seasons.append(season)
                break # only fetch first season found for now

    return seasons
        

def fetchEpisodes(id):
    feedEpisodes = []
    url = 'https://radio.nrk.no/psapi/series/dagsnytt/seasons/{}/Episodes'.format(id)
    with urllib.request.urlopen(url) as response:
        p = response.read()

        episodes = json.loads(p)

        for e in episodes:
            print("seasonId: {}, seriesTitle: {}, episodeId: {}, episode {}, title: {}, date: {}".format(e['seasonId'], e['seriesTitle'],  e['id'], e['episodeNumber'], e['episodeTitle'], e['episodeNumberOrDate']))
            try:
                publicationDate = e['firstTimeTransmitted']['actualTransmissionDate']
            except TypeError as e:
                publicationDate = None

            if publicationDate: 
                m = re.search('Date\(([^+]+)([^)]+)\)', publicationDate)
                if m:
                    dateString = m.group(1), m.group(2)
                    timestamp = float(dateString[0]) / 1000
                    timezone = dateString[1]
                    publicationDate = datetime.fromtimestamp(timestamp)
                    print("publicationDate: {}".format(publicationDate))
                    try:
                        assets = e['mediaAssetsOnDemand']

                        episode = {
                            'id': e['id'],
                            'title': "{}: {}".format(e['seriesTitle'], e['episodeTitle']),
                            'description': "{}{}".format(e['seasonId'], e['episodeNumber']),
                            'date': publicationDate,
                            'assets': assets
                        }
                        feedEpisodes.append(episode)
                    except TypeError as e:
                        print("No media assets: {}".format(e))

    return feedEpisodes

def getBestQualityAssets(assets):
    segmentUrls = []

    for asset in assets:
        playlistUrl = asset['hlsUrl']
        print("master playlist: {}".format(playlistUrl))

        masterPlaylist = m3u8.load(playlistUrl)

        # Master playlist contains playlists of different quality versions of
        # the same stream, just get the best one
        byBestQuality = masterPlaylist.playlists
        sorted(byBestQuality, key=lambda x: x.stream_info.bandwidth)
        bestQuality = byBestQuality.pop()

        assetPlaylistUrl = bestQuality.uri
        print("asset playlist: {}".format(assetPlaylistUrl))

        segmentPlaylist = m3u8.load(urljoin(playlistUrl, assetPlaylistUrl))
        for segment in segmentPlaylist.segments:
            segmentUrls.append(urljoin(playlistUrl, segment.uri))

    return segmentUrls

def getAssetsAsMp3(assets):
    with open("/tmp/testfile", "wb+") as tmp_file:
        for a in assets:
            with urllib.request.urlopen(a) as response:
                tmp_file.write(response.read())
        
    sourceAudio = AudioSegment.from_file(open("/tmp/testfile", "rb"), "aac")

    with tempfile.NamedTemporaryFile(delete=False) as mp3_file:
        sourceAudio.export(mp3_file, format="mp3")

        return mp3_file.read()

def generateFeed(seasons):
    season = seasons.pop()
    items = []

    for episode in season['episodes']:
        items.append(RSSItem(
            title = episode['title'],
            link = "{}/recode/{}/{}".format(appUrl, season['name'].lower(), episode['id']),
            description = episode['description'],
            guid = Guid("{}/rss/".format(appUrl), episode['id']),
            pubDate = episode['date']
        ))

    rss = RSS2(
        title = season['name'],
        link = appUrl,
        description = season['description'],

        lastBuildDate = datetime.utcnow(),

        items = items
    )

    return rss.to_xml()


