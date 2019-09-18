#!/bin/bash
sed -i "s/IP = 10.200.43.160/IP = $mongo_ip/g" /usr/src/project-server/configfile/config.ini
exec "$@"
