# Use an official Python runtime as a base image
FROM python:3.9-slim-buster

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt /app/

# Install any needed dependencies specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Flask application code into the container at /app
COPY . /app/

# Set environment variables
ENV GOOGLE_APPLICATION_CREDENTIALS="/app/application_default_credentials.json"

# Define the command to run your application
CMD ["flask", "--app", "app", "run", "--host=0.0.0.0"]
