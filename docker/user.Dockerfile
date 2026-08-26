FROM kumatea/telethon

# Set entrypoint
ENTRYPOINT ["/bin/sh", "/home/kuma/bots/jd/docker/run-preview.sh"]
