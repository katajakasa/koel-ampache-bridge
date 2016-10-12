# -*- coding: utf-8 -*-

import argparse
from getpass import getpass

from tables import db, User, BridgeUser
import config

from flask import Flask
import tabulate
from hashlib import sha256


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = config.KOEL_DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


def check_args(a):
    if not a.username:
        print("Username parameter is required for this operation.")
        return 1

    if a.username:
        if len(a.username) > 32 or len(a.username) < 4:
            print("Username must be between 4 and 32 characters long")
            return 1

    if a.password:
        if len(a.password) < 8:
            print("Password must at least 8 characters long")
            return 1

    return 0


def add_user(a):
    # Require password for new users. If one is not given vie commandline, get it here.
    if not a.password or a.password == '':
        a.password = getpass("Password: ")

    # Check inputs
    ret_val = check_args(a)
    if ret_val != 0:
        return ret_val

    # Make sure that koel user exists
    koel_user = User.get_one_or_none(name=a.username)
    if not koel_user:
        print("Koel user with name '{}' does not exist!".format(a.username))
        return 1

    # Create a bridge user
    bridge_user = BridgeUser()
    bridge_user.user = koel_user.id
    bridge_user.password = sha256(a.password).hexdigest()

    # Commit changes
    db.session.add(bridge_user)
    try:
        db.session.commit()
    except User.IntegrityError as e:
        print("Error: {}".format(e.message))
        return 1

    print("User {} succesfully added!".format(a.username))
    return 0


def list_users(a):
    userlist = []
    for bridge_user in BridgeUser.get_many():
        koel_user = User.get_one(id=bridge_user.user)
        ser = {
            'id': bridge_user.id,
            'username': koel_user.name,
            'email': koel_user.email,
        }
        userlist.append(ser)
    headers = {
        'id': 'ID',
        'username': 'Username',
        'email': 'Email',
    }
    print(tabulate.tabulate(userlist, headers, tablefmt="grid"))
    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Manage users for koel-ampache bridge')
    parser.add_argument('operation', nargs='+', choices=['add', 'list'], help='Operation')
    parser.add_argument('--username', type=str, help='Username')
    parser.add_argument('--password', type=str, nargs='?', help='Password', default='')
    args = parser.parse_args()

    db.init_app(app)
    with app.app_context():
        op = {
            'add': add_user,
            'list': list_users
        }[args.operation[0]]
        exit(op(args))
