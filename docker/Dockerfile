FROM kumatea/bot:latest

ENV CONDA_PKGS="aiohttp apscheduler beautifulsoup4 pillow pyrogram uvloop"
ENV PIP_PKGS="telethon chinesecalendar tgcrypto"

# Create conda environment
RUN set -ex && \
    eval "$(/opt/conda/bin/conda shell.bash hook)" && \
    conda create -n jd $CONDA_PKGS -y && \
    conda clean -afy && \
    conda activate jd && \
    pip install $PIP_PKGS --prefer-binary --extra-index-url https://ext.kmtea.eu/cdn && \
    rm -rf /root/.cache/*


# Set entrypoint
ENTRYPOINT ["/bin/bash", "/home/kuma/bots/jd/docker/run-docker.sh"]
