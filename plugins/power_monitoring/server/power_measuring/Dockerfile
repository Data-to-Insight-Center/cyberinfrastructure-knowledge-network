FROM nvcr.io/nvidia/l4t-base:r32.4.3

# Install necessary Python packages
RUN apt-get update && apt-get install -y \
    python3-pip \
    && pip3 install jetson-stats

# Copy your script into the container
COPY power_log_generator.py /app/

# Set the working directory
WORKDIR /app
