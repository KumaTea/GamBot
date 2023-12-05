# Basic Telegram Bot Configuration

FROM kumatea/bot:latest

# Create conda environment
RUN set -ex && \
    eval "$(/opt/conda/bin/conda shell.bash hook)" && \
    conda create -n jd pillow aiohttp pyrogram apscheduler uvloop -y && \
    conda clean -afy && \
    conda activate jd && \
    pip install telethon && \
    pip install tgcrypto 2>/dev/null || wget "https://github.com/KumaTea/NextBot/releases/download/1.0/TgCrypto-1.2.5-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl" && pip install ./TgCrypto-1.2.5-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl && rm ./TgCrypto-1.2.5-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl && \
    rm -rf /root/.cache/*


# Set entrypoint
ENTRYPOINT ["/bin/bash", "/home/kuma/bots/jd/docker/run-docker.sh"]
