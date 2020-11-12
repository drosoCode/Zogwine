#!/bin/bash
ldconfig
service nginx start
uwsgi --ini uwsgi.ini