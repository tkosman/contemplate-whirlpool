#!/bin/sh
set -e

# Default BACKEND_HOST is provided by ENV; fallback to host.docker.internal
: ${BACKEND_HOST:=host.docker.internal}

if [ -f /etc/nginx/templates/default.conf.template ]; then
  echo "Substituting BACKEND_HOST=${BACKEND_HOST} into nginx config"
  envsubst '${BACKEND_HOST}' < /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf
fi

exec nginx -g 'daemon off;'
