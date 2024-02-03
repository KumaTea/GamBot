# Basic Telegram Bot Configuration

FROM kumatea/bot:latest

# Create conda environment
RUN set -ex && \
    eval "$(/opt/conda/bin/conda shell.bash hook)" && \
    conda create -n jd aiohttp apscheduler beautifulsoup4 pillow pyrogram uvloop -y && \
    conda clean -afy && \
    conda activate jd && \
    pip install telethon chinesecalendar tgcrypto --extra-index-url https://ext.kmtea.eu/simple && \
    rm -rf /root/.cache/*


# Set entrypoint
ENTRYPOINT ["/bin/bash", "/home/kuma/bots/jd/docker/run-docker.sh"]
