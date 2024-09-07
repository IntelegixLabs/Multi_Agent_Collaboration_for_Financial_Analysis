# Build the base Docker image
docker build -f docker/Dockerfile.base -t financial-analysis-base-image .

# Run Docker Compose with the specified configuration file
docker-compose -f docker/docker-compose.yml up -d --build