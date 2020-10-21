#!/bin/bash
ldconfig
service nginx start
cd app && uwsgi --ini uwsgi.ini