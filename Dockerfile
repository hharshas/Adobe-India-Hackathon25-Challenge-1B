# Use a specific, stable Python version. slim is smaller.
# Specify the platform as required by the challenge.
FROM --platform=linux/amd64 python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# --- EXPLICITLY SET MODEL CACHE DIRECTORY ---
# This makes the model download process more robust by specifying a clear
# location for the cached models, avoiding potential permission issues.
ENV SENTENCE_TRANSFORMERS_HOME=/app/models

# Copy the requirements file first to leverage Docker layer caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# --- CRUCIAL STEP: PRE-DOWNLOAD MODELS FOR OFFLINE EXECUTION ---
# This runs during the 'docker build' step with network access.
# The models will be downloaded and saved to the directory specified by SENTENCE_TRANSFORMERS_HOME.
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
# Download all necessary NLTK data packages
RUN python -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab')"

# Copy the rest of your application code into the container
COPY . .

# Define the command that will run when the container starts
CMD ["python", "main.py"]
