# -*- coding: utf-8 -*-

import mimetypes
import os
from binascii import hexlify

from flask import Response, request
from werkzeug.datastructures import Headers
import audiotranscode

from tables import Song
import config


def stream_audio():
    song = Song.get_one(id=request.args.get('id'))

    # A hack to get my local dev env working
    path = song.path
    if config.DEBUG:
        cut = '/mnt/storage/audio/music/'
        path = os.path.join(config.MUSIC_DIR, song.path[len(cut):])

    # Find the file and guess type
    mime = mimetypes.guess_type(path)[0]
    size = os.path.getsize(path)

    # Send some extra headers
    headers = Headers()
    headers.add('Accept-Ranges', 'bytes')

    # See if we got range
    range_bytes = request.headers.get('Range')
    range_start = 0
    range_end = None
    if range_bytes:
        range_start, range_end = range_bytes[6:].split("-")
        try:
            range_end = int(range_end)
        except ValueError:
            range_end = None
        range_start = int(range_start)

    if not range_end or range_end >= size:
        range_end = size - 1

    # Make sure range_start and range_end are withing size limits
    if range_start >= size:
        return Response("", mimetype=mime, headers=headers, status=416)
    else:
        content_length = (range_end + 1) - range_start
        headers.add("Content-Length", content_length)
        headers.add("Content-Range", "bytes {}-{}/{}".format(range_start, range_end, size))
        status = 206

    def generate_audio():
        with open(path, "rb") as handle:
            handle.seek(range_start)
            left = content_length
            while left:
                r = 4096 if 4096 < left else left
                data = handle.read(4096)
                left -= r
                yield data
    return Response(generate_audio(), mimetype=mime, headers=headers, status=status)
