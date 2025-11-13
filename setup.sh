# setup.sh - Setup script for the project
#!/bin/bash

echo "Setting up Metadata Manager..."

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
echo "Creating superuser..."
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput

echo "Setup complete! Run 'python manage.py runserver' to start the application."