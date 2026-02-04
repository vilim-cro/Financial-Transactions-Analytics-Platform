"""Configuration settings for the user data update script."""
import os

# PostgreSQL configuration
# Use environment variables if set, otherwise default to Docker service names
# For local development, set POSTGRES_HOST=localhost, POSTGRES_PORT=5433
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5433"))
POSTGRES_DB = os.getenv("POSTGRES_DB", "all_users")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")

# Update configuration
UPDATE_PERCENTAGE = float(os.getenv("UPDATE_PERCENTAGE", "0.01"))

# Fields that can be updated
UPDATABLE_FIELDS = ["city", "job", "zip"]

# Random value pools
CITIES = [
    "New York", "Los Angeles", "Chicago", "Houston", "Phoenix",
    "Philadelphia", "San Antonio", "San Diego", "Dallas", "San Jose",
    "Austin", "Jacksonville", "San Francisco", "Columbus", "Fort Worth",
    "Charlotte", "Seattle", "Denver", "Boston", "El Paso",
    "Detroit", "Nashville", "Portland", "Oklahoma City", "Las Vegas",
    "Memphis", "Louisville", "Baltimore", "Milwaukee", "Albuquerque"
]

JOBS = [
    "Software Engineer", "Data Scientist", "Product Manager", "Marketing Manager",
    "Sales Representative", "Accountant", "Teacher", "Nurse", "Doctor",
    "Lawyer", "Consultant", "Designer", "Analyst", "Manager", "Director",
    "Engineer", "Developer", "Architect", "Administrator", "Specialist",
    "Coordinator", "Assistant", "Executive", "Supervisor", "Technician"
]

# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
