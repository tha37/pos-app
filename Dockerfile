# Base image
FROM python:3.10-slim

# Install wkhtmltopdf dependencies
RUN apt-get update -y && \
    apt-get install -y --no-install-recommends \
    libjpeg-dev zlib1g-dev libxext-dev libfontconfig1 libxrender1 xfonts-base xfonts-75dpi \
    && rm -rf /var/lib/apt/lists/*

# Install wkhtmltopdf itself
RUN wget https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6-1/wkhtmltox_0.12.6-1.bionic_amd64.deb
RUN dpkg -i wkhtmltox_0.12.6-1.bionic_amd64.deb || true
RUN apt-get install -f -y
RUN ln -s /usr/local/bin/wkhtmltopdf /usr/bin/wkhtmltopdf
RUN ln -s /usr/local/bin/wkhtmltoimage /usr/bin/wkhtmltoimage

# Working directory
WORKDIR /app

# Copy requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port the app runs on
EXPOSE 5000

# Command to run the application
CMD ["flask", "run", "--host=0.0.0.0"]
