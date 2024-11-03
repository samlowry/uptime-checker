# Use the official Playwright image
FROM mcr.microsoft.com/playwright/python:v1.48.0

# Set the working directory
WORKDIR /app

# Copy only the app folder
COPY app/ .

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port the app runs on
EXPOSE 5000

# Command to run your application
CMD ["python", "app.py"]  # Adjust this command based on your entry point
