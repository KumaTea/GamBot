FROM kumatea/telethon:web

ARG PIP_PKGS="apscheduler<3.11 chinesecalendar pillow"

# Install packages
RUN set -ex && \
    pip install $PIP_PKGS --prefer-binary --no-cache-dir --extra-index-url https://ext.kmtea.eu/cdn && \
    rm -rf /root/.cache

# Set entrypoint
ENTRYPOINT ["/bin/sh", "/home/kuma/bots/jd/docker/run-docker.sh"]
