git pull

# Create data directory if it doesn't exist
mkdir -p data
# Only run chown on Linux (Windows/Docker Desktop handles permissions automatically)
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    sudo chown -R 10001:10001 data
fi

docker build -t image-hashtag-api:cpu .

docker stop image-hashtag-api || true
docker rm image-hashtag-api || true

docker run -d \
  -p 6868:6868 \
  -e PORT=6868 \
  -v "$(pwd)/data:/data" \
  --restart unless-stopped \
  --name image-hashtag-api \
  image-hashtag-api:cpu
