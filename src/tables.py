# -*- coding: utf-8 -*-

from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Boolean, Text, Float
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class ModelHelperMixin(object):
    @classmethod
    def get_one(cls, **kwargs):
        return cls.query.filter_by(**kwargs).one()

    @classmethod
    def get_one_or_none(cls, **kwargs):
        return cls.query.filter_by(**kwargs).one_or_none()

    @classmethod
    def get_many(cls, **kwargs):
        return cls.query.filter_by(**kwargs).all()

    @classmethod
    def delete(cls, **kwargs):
        cls.query.filter_by(**kwargs).delete()


class Artist(db.Model, ModelHelperMixin):
    __tablename__ = "artists"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    image = Column(String(255), nullable=False)
    created_at = Column(DateTime, nullable=True, default=None)
    updated_at = Column(DateTime, nullable=True, default=None)


class Album(db.Model, ModelHelperMixin):
    __tablename__ = "albums"
    id = Column(Integer, primary_key=True)
    artist_id = Column(ForeignKey('artists.id'), nullable=False)
    name = Column(String(255), nullable=False)
    cover = Column(String(255), nullable=False, default='')
    is_compilation = Column(Boolean, default=None, nullable=True)
    created_at = Column(DateTime, nullable=True, default=None)
    updated_at = Column(DateTime, nullable=True, default=None)


class Song(db.Model, ModelHelperMixin):
    __tablename__ = "songs"
    id = Column(String(32), primary_key=True, nullable=False)
    album_id = Column(ForeignKey('albums.id'), nullable=False)
    contributing_artist_id = Column(ForeignKey('artists.id'), nullable=True, default=None)
    title = Column(String(255), nullable=False)
    length = Column(Float, nullable=False)
    track = Column(Integer, default=None, nullable=True)
    lyrics = Column(Text, nullable=False, default='')
    path = Column(Text, nullable=False)
    mtime = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=True, default=None)
    updated_at = Column(DateTime, nullable=True, default=None)


class User(db.Model, ModelHelperMixin):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    password = Column(String(60), nullable=False)
    is_admin = Column(Integer, nullable=False, default=0)
    preferences = Column(Text, nullable=True)
    remember_token = Column(String(100), default=None, nullable=True)
    created_at = Column(DateTime, nullable=True, default=None)
    updated_at = Column(DateTime, nullable=True, default=None)


class BridgeUser(db.Model, ModelHelperMixin):
    __tablename__ = "bridge_user"
    id = Column(Integer, primary_key=True)
    user = Column(ForeignKey('users.id'), nullable=False)
    password = Column(String(64), nullable=False)  # This must be a sha256 password


class BridgeSession(db.Model, ModelHelperMixin):
    __tablename__ = "bridge_session"
    id = Column(String(32), primary_key=True, nullable=False)
    bridge_user = Column(ForeignKey('bridge_user.id'), nullable=False)
    created_at = Column(DateTime, nullable=True, default=None)
    updated_at = Column(DateTime, nullable=True, default=None)
