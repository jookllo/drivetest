# Build from the repository root: the importer also requires signs/.
FROM php:8.3-apache-bookworm@sha256:b79a53c3fb1dd4b9f350a8d99d84951512b6c21044e61bbecfee8af030b3722e

RUN apt-get update \
    && apt-get install -y --no-install-recommends unzip libonig-dev libzip-dev libicu-dev \
    && docker-php-ext-install -j"$(nproc)" pdo_mysql mbstring zip intl bcmath opcache \
    && a2enmod rewrite \
    && rm -rf /var/lib/apt/lists/*

COPY --from=composer:2@sha256:af98f42dfff7c68ba8d53c2164fd9fde1087b7d449514baa38c418b1f6bc4bac /usr/bin/composer /usr/local/bin/composer
WORKDIR /app/api
COPY api/ /app/api/
COPY signs/manifest.json /app/signs/manifest.json
COPY signs/svg/ /app/signs/svg/
COPY sign-labels.json /app/sign-labels.json
COPY api/docker/apache.conf /etc/apache2/sites-available/000-default.conf
COPY api/docker/php.ini /usr/local/etc/php/conf.d/drivetest.ini
COPY api/docker/start.sh /usr/local/bin/drivetest-start

RUN mkdir -p storage/app/private storage/framework/cache/data \
      storage/framework/sessions storage/framework/views storage/logs bootstrap/cache \
    && COMPOSER_ALLOW_SUPERUSER=1 composer install \
      --no-dev --prefer-dist --no-interaction --optimize-autoloader \
    && composer check-platform-reqs --no-dev \
    && chmod +x /usr/local/bin/drivetest-start \
    && chown -R www-data:www-data storage bootstrap/cache

EXPOSE 80
CMD ["/usr/local/bin/drivetest-start"]
