# -*- coding: utf-8 -*-

import xml.etree.cElementTree as Etree
from tables import Artist, Album, Song, BridgeSong
import config
from utils import read_music_title


def render_album(n_root, album):
    artist = Artist.get_one(id=album.artist_id)

    a_node = Etree.SubElement(n_root, "album", id=str(album.id))
    Etree.SubElement(a_node, "name").text = album.name
    Etree.SubElement(a_node, "artist", id=str(artist.id)).text = artist.name
    Etree.SubElement(a_node, "tracks").text = str(Song.query.filter(Song.album_id == album.id).count())
    if album.cover:
        Etree.SubElement(a_node, "art").text = "{}{}".format(config.BRIDGE_COVERS, album.cover)


def render_artist(n_root, artist):
    a_node = Etree.SubElement(n_root, "artist", id=str(artist.id))
    Etree.SubElement(a_node, "name").text = artist.name
    Etree.SubElement(a_node, "albums").text = str(Album.query.filter(Album.artist_id == artist.id).count())
    Etree.SubElement(a_node, "songs").text = str(Song.query.filter(Song.contributing_artist_id == artist.id).count())


def render_song(n_root, song, bridge_song=None):
    artist = Artist.get_one_or_none(id=song.contributing_artist_id)
    album = Album.get_one_or_none(id=song.album_id)
    if not bridge_song:
        bridge_song = BridgeSong.get_one(song_id=song.id)

    a_node = Etree.SubElement(n_root, "song", id=str(bridge_song.id))

    if not song.title or len(song.title) == 0:
        song.title = read_music_title(song.path)
    Etree.SubElement(a_node, "title").text = song.title

    if song.track:
        Etree.SubElement(a_node, "track").text = str(song.track)

    Etree.SubElement(a_node, "url").text = "{}?id={}".format(config.BRIDGE_PLAY, song.id)
    Etree.SubElement(a_node, "length").text = str(int(round(song.length)))
    if artist:
        Etree.SubElement(a_node, "artist", id=str(artist.id)).text = artist.name
    if album:
        Etree.SubElement(a_node, "album", id=str(album.id)).text = album.name
    if album.cover:
        Etree.SubElement(a_node, "art").text = "{}{}".format(config.BRIDGE_COVERS, album.cover)
