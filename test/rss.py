#!/usr/bin/env python3
import json, re
from datetime import datetime
import pytz
import sys
import m3u8

def fetchSeasons(name):
    url = 'https://radio.nrk.no/psapi/series/%s' % ( name )
    url = name # temp
    with open(url) as f:
        p = f.read()
        
        playlist = json.loads(p)

        print("{}, {}".format(playlist['title'], playlist['description']))

        for s in playlist['seasons']:
            if s['hasOnDemandRightsEpisodes']:
                print("%s: %s (%s)".format(s['id'], s['name'], url))

                episodes = fetchEpisodes(s['id'])
                print(episodes)
                break


def fetchEpisodes(id):
    url = 'https://radio.nrk.no/psapi/series/dagsnytt/seasons/{}/Episodes'.format(id)
    url = 'Episodes' # temp
    with open(url) as f:
        p = f.read()

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
                        for asset in e['mediaAssetsOnDemand']:
                            print("media assets: {}".format(asset['hlsUrl']))
                            master = m3u8.load("master.m3u8")
                            for playlist in master.playlists:
                                print(playlist.uri)
                                streamdata = m3u8.load("index_0_a.m3u8")
                                for segment in streamdata.segments:
                                    print(segment.uri)
                            sys.exit()

                    except TypeError as e:
                        print("No media assets: {}".format(e))



index = fetchSeasons('dagsnytt')
