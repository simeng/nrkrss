# Convert a NRK radio show url to an RSS feed

NRK suddenly stopped supporting podcast for its news stream so I started this to get it back.
This is work in progress.

The plan is:
* List episodes as RSS
* When opening the media url in the RSS, convert the aac over hsl directly to an mp3 stream

## Dependencies

* python3
* python3-pydub # convert to mp3
* python3-m3u8 # read m3u8 playlist format

