# -*- coding: utf-8 -*-

import mimetypes
import os

from flask import Response, request
from werkzeug.datastructures import Headers
import audiotranscode

from utils import generate_random_key
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
    ext = mimetypes.guess_extension(mime)

    # Transcoding if required
    transcode = False
    if ext not in ['.mp3', '.ogg']:
        transcode = True
        mime = "audio/mpeg"

    # Send some extra headers
    headers = Headers()
    headers.add('Content-Transfer-Encoding', 'binary')
    headers.add('Content-Length', os.path.getsize(path))

    def generate_audio():
        if not transcode:
            with open(path, "rb") as handle:
                data = handle.read(1024)
                while data:
                    yield data
                    data = handle.read(1024)
        else:
            tc = audiotranscode.AudioTranscode()
            for data in tc.transcode_stream(path, 'mp3'):
                yield data
    return Response(generate_audio(), mimetype=mime, headers=headers)
