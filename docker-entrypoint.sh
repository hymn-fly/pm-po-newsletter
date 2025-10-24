#!/bin/sh
set -eu

PORT_VALUE=${PORT:-80}
export PORT="$PORT_VALUE"

# Detect Railway env to set sensible FastAPI default upstream
if [ -n "${RAILWAY_ENVIRONMENT_ID:-}" ]; then
    DEFAULT_FASTAPI_UPSTREAM="http://pm-po-newsletter.railway.internal:8000"
else
    DEFAULT_FASTAPI_UPSTREAM="http://host.docker.internal:8000"
fi

FASTAPI_UPSTREAM_VALUE=${FASTAPI_UPSTREAM:-$DEFAULT_FASTAPI_UPSTREAM}
export FASTAPI_UPSTREAM="$FASTAPI_UPSTREAM_VALUE"

envsubst '${PORT} ${FASTAPI_UPSTREAM}' < /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf

exec nginx -g 'daemon off;'
