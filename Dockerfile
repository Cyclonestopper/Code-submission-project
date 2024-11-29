# Use an official Python image as the base (with Debian for g++)
FROM python:3.9-slim

# Install system dependencies (g++ and others)
RUN apt-get update && apt-get install -y g++

# Set the working directory inside the container
WORKDIR /app

# Copy your project files into the container
COPY . /app

# Install Python dependencies
RUN pip install -r Problem_1/app/api/requirements.txt

# Expose the port your Flask app will run on
EXPOSE 3000

# Define the command to run your Flask app
CMD ["python", "Problem_1/app/api/index.py"]
