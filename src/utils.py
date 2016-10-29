import os
import binascii
import mutagen


def generate_random_key():
    return binascii.hexlify(os.urandom(16))


def read_music_title(path):
    title_tags = (
        u'©nam', 'TXXX:TITLE', 'TIT2', 'Title', 'TITLE', 'TRACK TITLE', 'TRACKTITLE', 'TrackTitle', 'Track Title'
    )
    try:
        m = mutagen.File(path)
        for tag in title_tags:
            try:
                return unicode(m[tag][0])
            except KeyError:
                pass
            except ValueError:
                pass
    except mutagen.MutagenError:
        pass
    return 'N/A'
