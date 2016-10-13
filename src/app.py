# -*- coding: utf-8 -*-

from flask import request, Response
import arrow
from sqlalchemy.orm.exc import NoResultFound

import xml.etree.cElementTree as Etree
import hashlib
from datetime import datetime

from utils import generate_random_key
from tables import Artist, Album, Song, BridgeSession, BridgeUser, User, db
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
    Etree.SubElement(n_root, "songs").text = "0"
    Etree.SubElement(n_root, "artists").text = "0"
    Etree.SubElement(n_root, "albums").text = "0"
    Etree.SubElement(n_root, "tags").text = "0"
    Etree.SubElement(n_root, "videos").text = "0"
    return n_root


def do_ping():
    n_root = Etree.Element("root")
    Etree.SubElement(n_root, "version").text = config.VERSION
    return n_root


@is_authenticated
def do_artists():
    limit = request.args.get('limit', 0)

    n_root = Etree.Element("root")
    for artist in Artist.get_many():
        a_node = Etree.SubElement(n_root, "artist", id=str(artist.id))
        Etree.SubElement(a_node, "name").text = artist.name
        Etree.SubElement(a_node, "albums").text = "0"
        Etree.SubElement(a_node, "songs").text = "0"

    return n_root


@is_authenticated
def do_albums():
    n_root = Etree.Element("root")
    for album in Album.get_many():
        artist = Artist.get_one(id=album.artist_id)

        a_node = Etree.SubElement(n_root, "album", id=str(album.id))
        Etree.SubElement(a_node, "name").text = album.name
        Etree.SubElement(a_node, "artist", id=str(artist.id)).text = artist.name
        if album.cover:
            Etree.SubElement(a_node, "art").text = "{}{}".format(config.BRIDGE_COVERS, album.cover)
    return n_root


@is_authenticated
def do_playlists():
    n_root = Etree.Element("root")
    return n_root


@is_authenticated
def do_artist_albums():
    limit = request.args.get('limit', 0)
    artist_filter = request.args.get('filter', 0)

    n_root = Etree.Element("root")
    for album in Album.get_many(artist_id=artist_filter):
        artist = Artist.get_one(id=album.artist_id)

        a_node = Etree.SubElement(n_root, "album", id=str(album.id))
        Etree.SubElement(a_node, "name").text = album.name
        Etree.SubElement(a_node, "artist", id=str(artist.id)).text = artist.name
        if album.cover:
            Etree.SubElement(a_node, "art").text = "{}{}".format(config.BRIDGE_COVERS, album.cover)

    return n_root


@is_authenticated
def do_album_songs():
    limit = request.args.get('limit', 0)
    album_filter = request.args.get('filter', 0)

    n_root = Etree.Element("root")
    for song in Song.get_many(album_id=album_filter):
        artist = Artist.get_one_or_none(id=song.contributing_artist_id)
        album = Album.get_one_or_none(id=song.album_id)

        a_node = Etree.SubElement(n_root, "song", id=str(song.id))
        Etree.SubElement(a_node, "title").text = song.title
        Etree.SubElement(a_node, "url").text = "{}?id={}".format(config.BRIDGE_PLAY, song.id)
        if artist:
            Etree.SubElement(a_node, "artist").text = artist.name
        if album:
            Etree.SubElement(a_node, "album").text = album.name
        if album.cover:
            Etree.SubElement(a_node, "art").text = "{}{}".format(config.BRIDGE_COVERS, album.cover)

    return n_root


# Route request to the correct place
def route_action():
    action = request.args.get('action')
    try:
        e_root = {
            'handshake': do_handshake,
            'ping': do_ping,
            'artists': do_artists,
            'albums': do_albums,
            'playlists': do_playlists,
            'artist_albums': do_artist_albums,
            'album_songs': do_album_songs
        }[action]()
    except KeyError:
        e_root = Etree.Element("root")
        Etree.SubElement(e_root, "error", code="405").text = "Feature not implemented"

    output = Etree.tostring(e_root, encoding='UTF-8')
    if config.DEBUG:
        print(output)
    return Response(output, mimetype='application/xml')


