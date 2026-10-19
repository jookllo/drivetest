#!/bin/sh
set -eu
cd /app/api
if [ -z "${APP_KEY:-}" ]; then
    echo 'APP_KEY must be supplied as a runtime environment variable.' >&2
    exit 1
fi
mkdir -p storage/app/private storage/framework/cache/data \
    storage/framework/sessions storage/framework/views storage/logs bootstrap/cache
chown -R www-data:www-data storage bootstrap/cache
su -s /bin/sh www-data -c 'php artisan config:cache && php artisan view:cache'
exec apache2-foreground
