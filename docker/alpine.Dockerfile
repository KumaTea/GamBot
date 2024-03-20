FROM kumatea/pyrogram:alpine

ENV PIP_PKGS="aiohttp apscheduler beautifulsoup4 pillow telethon chinesecalendar tgcrypto"

# Install packages
RUN set -ex && \
    pip install $PIP_PKGS --prefer-binary --no-cache-dir && \
    (rm -rf /root/.cache || echo "No cache in .cache")


# Set entrypoint
ENTRYPOINT ["/bin/sh", "/home/kuma/bots/jd/docker/run-docker.sh"]
