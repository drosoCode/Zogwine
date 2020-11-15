#!/bin/bash
ldconfig
service nginx restart
uwsgi --ini uwsgi.ini