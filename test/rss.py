#!/usr/bin/env python3
import json, re
from datetime import datetime
import sys
import m3u8
from pydub import AudioSegment
from PyRSS2Gen import RSS2, RSSItem, Guid

def fetchSeasons(name):
    seasons = []

    url = 'https://radio.nrk.no/psapi/series/%s' % ( name )
    url = name # temp
    with open(url) as f:
        p = f.read()
        
        playlist = json.loads(p)

        print("{}, {}".format(playlist['title'], playlist['description']))
        season = {
            'title': playlist['title'],
            'description': playlist['description'],
            'episodes': []
        }

        for s in playlist['seasons']:
            if s['hasOnDemandRightsEpisodes']:
                print("%s: %s (%s)".format(s['id'], s['name'], url))

                episodes = fetchEpisodes(s['id'])
                season['episodes'] = episodes
                seasons.append(season)
                break

    return seasons
        

def fetchEpisodes(id):
    feedEpisodes = []
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
                        assets = getBestQualityAssets(e['mediaAssetsOnDemand'])

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
        playlistUrl = "master.m3u8" #temp
        print("master playlist: {}".format(playlistUrl))

        masterPlaylist = m3u8.load(playlistUrl)

        # Master playlist contains playlists of different quality versions of
        # the same stream, just get the best one
        byBestQuality = masterPlaylist.playlists
        sorted(byBestQuality, key=lambda x: x.stream_info.bandwidth)
        bestQuality = byBestQuality.pop()

        assetPlaylistUrl = bestQuality.uri
        assetPlaylistUrl = "index_0_a.m3u8"
        print("asset playlist: {}".format(assetPlaylistUrl))

        segmentPlaylist = m3u8.load(assetPlaylistUrl)
        for segment in segmentPlaylist.segments:
            segmentUrls.append(segment.uri)

    return segmentUrls

def getSegmentsAsMp3(segments):
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        for s in segments:
            with urllib.request.urlopen(s) as response:
                tmp_file.write(response.read())

        sourceAudio = AudioSegment.from_aac(tmp_file)

        with tempfile.NamedTemporaryFile(delete=False) as mp3_file:
            sourceAudio.export(mp3_file, format="mp3")

            return mp3_file.read()

def generateFeed(seasons):
    season = seasons.pop()
    items = []

    for episode in season['episodes']:
        items.append(RSSItem(
            title = episode['title'],
            link = "https://radio.h4x.no/recode/{}".format(episode['id']),
            description = episode['description'],
            guid = Guid("https://radio.h4x.no/rss/", episode['id']),
            pubDate = episode['date']
        ))

    rss = RSS2(
        title = season['title'],
        link = "https://radio.h4x.no",
        description = season['description'],

        lastBuildDate = datetime.utcnow(),

        items = items
    )

    rss.write_xml(sys.stdout)


seasons = fetchSeasons('dagsnytt')
generateFeed(seasons)

