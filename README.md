# koel-ampache-bridge

Hacky ampache protocol bridge for Koel (see: http://koel.phanan.net/)

1. Rename src/config.py-dist to src/config.py and make your configs
2. Create user with "python src/manage_users.py"
3. Install at least lame, flac, ogg
4. Set up with eg. uWSGI. There is a uwsgi example config in the project root
5. Set up nginx/apache/whatever to redirect http://<mydomain>/server to the bridge
6. ???
7. Profit!

This is very hacky, I don't intend to support this in any way. If you
run into trouble, you are on your own :)

Use at your own peril!

License is MIT, do whatever.

