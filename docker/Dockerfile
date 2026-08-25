FROM kumatea/telethon:latest

ENV PIP_PKGS="aiohttp apscheduler<3.11 beautifulsoup4 chinesecalendar pillow requests tqdm"

# Install packages
RUN set -ex && \
    pip install $PIP_PKGS --prefer-binary --no-cache-dir --extra-index-url https://ext.kmtea.eu/cdn && \
    (rm -rf /root/.cache || echo "No cache in .cache")


# Set entrypoint
ENTRYPOINT ["/bin/sh", "/home/kuma/bots/jd/docker/run-docker.sh"]
