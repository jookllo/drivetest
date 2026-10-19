#!/usr/bin/env bash
# Disposable infrastructure only; never connects to the project's local MySQL.
set -euo pipefail
image=${1:?Usage: smoke.sh IMAGE}
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
run_id="drivetest-smoke-$$-$RANDOM"
network="$run_id-network"
mysql="$run_id-mysql"
app="$run_id-app"
volume="$run_id-private"
state=$(mktemp)
cleanup() {
    result=$?
    trap - EXIT
    if [ "$result" -ne 0 ]; then
        docker logs --tail 60 "$app" 2>/dev/null || true
        docker logs --tail 30 "$mysql" 2>/dev/null || true
    fi
    docker rm -fv "$app" "$mysql" >/dev/null 2>&1 || true
    docker volume rm "$volume" >/dev/null 2>&1 || true
    docker network rm "$network" >/dev/null 2>&1 || true
    rm -f "$state"
    exit "$result"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

docker network create "$network" >/dev/null
docker volume create "$volume" >/dev/null
docker run -d --name "$mysql" --network "$network" \
    -e MYSQL_DATABASE=drivetest_test -e MYSQL_USER=drivetest_ci \
    -e MYSQL_PASSWORD=ci-disposable-password -e MYSQL_ROOT_PASSWORD=ci-disposable-root-password \
    --health-cmd='mysqladmin ping -h 127.0.0.1 --silent' \
    --health-interval=2s --health-timeout=5s --health-retries=60 \
    mysql:8.0 >/dev/null
for attempt in $(seq 1 90); do
    if [ "$(docker inspect -f '{{.State.Health.Status}}' "$mysql")" = healthy ]; then break; fi
    sleep 2
done
[ "$(docker inspect -f '{{.State.Health.Status}}' "$mysql")" = healthy ]
key="base64:$(openssl rand -base64 32)"
# Only this disposable loopback-bound test container trusts all proxy headers.
docker run -d --name "$app" --network "$network" -p 127.0.0.1::80 \
    -v "$volume:/app/api/storage/app/private" \
    -e APP_ENV=production -e APP_DEBUG=false -e APP_KEY="$key" \
    -e APP_URL=https://localhost -e LOG_CHANNEL=stderr -e TRUSTED_PROXIES='*' \
    -e DB_CONNECTION=mysql -e DB_HOST="$mysql" -e DB_DATABASE=drivetest_test \
    -e DB_USERNAME=drivetest_ci -e DB_PASSWORD=ci-disposable-password \
    -e SESSION_DRIVER=database -e SESSION_ENCRYPT=true -e SESSION_SECURE_COOKIE=true \
    -e CACHE_STORE=database -e QUEUE_CONNECTION=sync "$image" >/dev/null
wait_for_app() {
    for attempt in $(seq 1 60); do
        if docker exec "$app" test -f /app/api/bootstrap/cache/config.php && \
            docker exec "$app" php -r '$s = @fsockopen("127.0.0.1", 80); exit($s ? 0 : 1);'; then return; fi
        sleep 2
    done
    return 1
}
wait_for_app
docker exec "$app" test ! -f /app/api/.env
docker exec "$app" test ! -d /app/api/tests
docker exec "$app" test ! -f /app/api/database/seeders/QuizBrowserSeeder.php
docker exec --user www-data "$app" php artisan migrate --force --no-interaction
docker exec --user www-data "$app" php artisan signs:import /app/sign-labels.json --dry-run
docker exec --user www-data "$app" php artisan signs:import /app/sign-labels.json
docker exec --user www-data "$app" test -s /app/api/storage/app/private/signs/r01-stop.svg
docker exec --user www-data "$app" php artisan schedule:list
port=$(docker port "$app" 80/tcp | head -1 | cut -d: -f2)
python3 "$script_dir/smoke.py" "http://127.0.0.1:$port" "$state" initial
# Config is rebuilt on restart; private volume and database sessions must survive.
docker restart "$app" >/dev/null
wait_for_app
# Docker may assign a new ephemeral host port after restart.
port=$(docker port "$app" 80/tcp | head -1 | cut -d: -f2)
docker exec --user www-data "$app" test -s /app/api/storage/app/private/signs/r01-stop.svg
python3 "$script_dir/smoke.py" "http://127.0.0.1:$port" "$state" restarted
echo 'Production image smoke checks passed.'
