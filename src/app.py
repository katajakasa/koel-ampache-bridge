# -*- coding: utf-8 -*-

from flask import request, Response
import arrow
from sqlalchemy.orm.exc import NoResultFound

import xml.etree.cElementTree as Etree
import hashlib
from datetime import datetime

from utils import generate_random_key
from tables import Artist, Album, Song, BridgeSession, BridgeUser, BridgeSong, User, db
from renderers import render_album, render_artist, render_song
import config


def is_authenticated(method):
    """ Checks if token is authenticated
    """
    def inner(*args, **kwargs):
        session = BridgeSession.get_one_or_none(id=request.args.get('auth'))
        if session:
            request.bridge_user = BridgeUser.get_one_or_none(id=session.bridge_user)
            return method(*args, **kwargs)
        else:
            n_root = Etree.Element("root")
            Etree.SubElement(n_root, "error", code="403").text = "Not authenticated"
            return n_root
    return inner


def do_handshake():
    auth = request.args.get('auth')
    timestamp = request.args.get('timestamp')
    user = request.args.get('user')

    n_root = Etree.Element("root")

    # Check username and find correct user
    try:
        koel_user = User.get_one(name=user)
        bridge_user = BridgeUser.get_one(id=koel_user.id)
    except NoResultFound:
        Etree.SubElement(n_root, "error", code="401").text = "Invalid login"
        return n_root

    # Check password
    m_hash = hashlib.sha256()
    m_hash.update(timestamp)
    m_hash.update(bridge_user.password)
    auth_cmp = m_hash.hexdigest()
    if auth != auth_cmp:
        Etree.SubElement(n_root, "error", code="401").text = "Invalid login"
        return n_root

    # Generate a new session
    session_key = generate_random_key()
    ses = BridgeSession()
    ses.bridge_user = bridge_user.id
    ses.id = session_key
    db.session.add(ses)
    db.session.commit()

    # Respond appropriately
    ts = datetime.now()
    Etree.SubElement(n_root, "version").text = config.VERSION
    Etree.SubElement(n_root, "auth").text = session_key
    Etree.SubElement(n_root, "update").text = arrow.get(ts).isoformat()
    Etree.SubElement(n_root, "add").text = arrow.get(ts).isoformat()
    Etree.SubElement(n_root, "clean").text = arrow.get(ts).isoformat()
    Etree.SubElement(n_root, "songs").text = str(Song.query.count())
    Etree.SubElement(n_root, "artists").text = str(Artist.query.count())
    Etree.SubElement(n_root, "albums").text = str(Album.query.count())
    Etree.SubElement(n_root, "tags").text = "0"
    Etree.SubElement(n_root, "videos").text = "0"
    return n_root


def do_ping():
    n_root = Etree.Element("root")
    Etree.SubElement(n_root, "version").text = config.VERSION
    return n_root


@is_authenticated
def do_artists():
    n_root = Etree.Element("root")
    for artist in Artist.get_many():
        render_artist(n_root, artist)
    return n_root


@is_authenticated
def do_artist():
    artist_filter = int(request.args.get('filter', 0))

    n_root = Etree.Element("root")
    artist = Artist.get_one(id=artist_filter)
    render_artist(n_root, artist)

    return n_root


@is_authenticated
def do_albums():
    n_root = Etree.Element("root")
    for album in Album.get_many():
        render_album(n_root, album)
    return n_root


@is_authenticated
def do_album():
    album_filter = int(request.args.get('filter', 0))

    n_root = Etree.Element("root")
    album = Album.get_one(id=album_filter)
    render_album(n_root, album)

    return n_root


@is_authenticated
def do_playlists():
    n_root = Etree.Element("root")
    return n_root


@is_authenticated
def do_playlist():
    n_root = Etree.Element("root")
    return n_root


@is_authenticated
def do_artist_albums():
    artist_filter = int(request.args.get('filter', 0))

    n_root = Etree.Element("root")
    for album in Album.get_many(artist_id=artist_filter):
        render_album(n_root, album)

    return n_root


def ensure_bridge_song(song):
    try:
        bs = BridgeSong.get_one(song_id=song.id)
    except NoResultFound:
        bs = BridgeSong()
        bs.song_id = song.id
        db.session.add(bs)
        db.session.commit()
    return bs


@is_authenticated
def do_album_songs():
    album_filter = int(request.args.get('filter', 0))

    n_root = Etree.Element("root")
    for song in Song.get_many(album_id=album_filter):
        bridge_song = ensure_bridge_song(song)
        render_song(n_root, song, bridge_song=bridge_song)

    return n_root


@is_authenticated
def do_artist_songs():
    artist_filter = int(request.args.get('filter', 0))

    n_root = Etree.Element("root")
    for song in Song.get_many(contributing_artist_id=artist_filter):
        bridge_song = ensure_bridge_song(song)
        render_song(n_root, song, bridge_song=bridge_song)

    return n_root


@is_authenticated
def do_song():
    song_filter = int(request.args.get('filter', 0))

    # Bridge song is hacky POS, but required because some players expect Integer ID's
    # and koel uses hash strings
    bridge_song = BridgeSong.get_one(id=song_filter)
    song = Song.get_one(id=bridge_song.song_id)
    n_root = Etree.Element("root")
    render_song(n_root, song, bridge_song=bridge_song)

    return n_root


@is_authenticated
def url_to_song():
    url = request.args.get('url', '')
    prefix = "{}?id=".format(config.BRIDGE_PLAY)

    print(url[len(prefix):])
    song = Song.get_one(id=url[len(prefix):])
    bridge_song = BridgeSong.get_one(song_id=song.id)

    n_root = Etree.Element("root")
    render_song(n_root, song, bridge_song=bridge_song)

    return n_root


# Route request to the correct place
def route_action():
    action = request.args.get('action')
    try:
        e_root = {
            'handshake': do_handshake,
            'ping': do_ping,
            'artists': do_artists,
            'artist': do_artist,
            'albums': do_albums,
            'album': do_album,
            'playlists': do_playlists,
            'playlist': do_playlist,
            'artist_albums': do_artist_albums,
            'song': do_song,
            'album_songs': do_album_songs,
            'artist_songs': do_artist_songs,
            'url_to_song': url_to_song
        }[action]()
    except KeyError:
        e_root = Etree.Element("root")
        Etree.SubElement(e_root, "error", code="405").text = "Feature not implemented"

    output = Etree.tostring(e_root, encoding='UTF-8')
    if config.DEBUG:
        print(output)
    return Response(output, mimetype='application/xml')


