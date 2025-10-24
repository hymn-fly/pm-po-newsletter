#!/bin/sh
set -eu

PORT_VALUE=${PORT:-80}
export PORT="$PORT_VALUE"

FASTAPI_UPSTREAM_VALUE=${FASTAPI_UPSTREAM:-http://host.docker.internal:8000}
export FASTAPI_UPSTREAM="$FASTAPI_UPSTREAM_VALUE"

envsubst '${PORT} ${FASTAPI_UPSTREAM}' < /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf

exec nginx -g 'daemon off;'
