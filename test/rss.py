import json, re
from datetime import datetime
import pytz


def fetchSeasons(name):
    url = 'https://radio.nrk.no/psapi/series/%s' % ( name )
    url = name # temp
    with open(url) as f:
        p = f.read()
        
        playlist = json.loads(p)

        print "%s, %s" % (playlist['title'], playlist['description'])

        for s in playlist['seasons']:
            if s['hasOnDemandRightsEpisodes']:
                print "%s: %s (%s)" % (s['id'], s['name'], url)

                episodes = fetchEpisodes(s['id'])
                print episodes
                break


def fetchEpisodes(id):
    url = 'https://radio.nrk.no/psapi/series/dagsnytt/seasons/%s/Episodes' % ( id )
    url = 'Episodes' # temp
    with open(url) as f:
        p = f.read()

        episodes = json.loads(p)

        for e in episodes:
            print "seasonId: %s, seriesTitle: %s, episodeId: %s, episode %d, title: %s, date: %s" % ( e['seasonId'], e['seriesTitle'],  e['id'], e['episodeNumber'], e['episodeTitle'], e['episodeNumberOrDate'] )
            try:
                publicationDate = e['firstTimeTransmitted']['actualTransmissionDate']
            except TypeError, e:
                publicationDate = None

            if publicationDate: 
                m = re.search('Date\(([^+]+)([^)]+)\)', publicationDate)
                if m:
                    dateString = m.group(1), m.group(2)
                    timestamp = float(dateString[0]) / 1000
                    timezone = dateString[1]
                    publicationDate = datetime.fromtimestamp(timestamp)
                    print "publicationDate: %s" % ( publicationDate )

index = fetchSeasons('dagsnytt')
