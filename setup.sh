#!/bin/bash

echo "Setting up Credit Approval System..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "Building and starting services..."
docker-compose up --build -d

echo "Waiting for services to be ready..."
sleep 30

echo "Running database migrations..."
docker-compose exec web python manage.py migrate

echo "Ingesting initial data..."
docker-compose exec web python manage.py ingest_data

echo "Setup complete!"
echo "The application is now running at:"
echo "- API: http://localhost:8000/api/"
echo "- Admin: http://localhost:8000/admin/"
echo ""
echo "To stop the services, run: docker-compose down" 