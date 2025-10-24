#!/bin/sh
set -eu

PORT_VALUE=${PORT:-80}
export PORT="$PORT_VALUE"

envsubst '${PORT}' < /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf

exec nginx -g 'daemon off;'
