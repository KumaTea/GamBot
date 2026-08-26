# Build Tips

```shell
cd bots
cd jd
cd docker

docker build -t kumatea/jd .
docker build -t kumatea/jd:preview -f user.Dockerfile .

docker run --name=jd --restart=unless-stopped -v /home/kuma/bots/jd:/home/kuma/bots/jd -d kumatea/jd
docker run --name=jd-preview --restart=unless-stopped -v /home/kuma/bots/jd:/home/kuma/bots/jd -d kumatea/jd:preview
```
