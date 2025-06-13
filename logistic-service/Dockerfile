# Gunakan base image Python
FROM python:3.11-slim

# Set working directory di dalam container
WORKDIR /app

# Copy semua file ke container
COPY . /app

# Buat folder instance untuk menyimpan database
RUN mkdir -p /app/instance

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port Flask (default 5000)
EXPOSE 5000

# Jalankan aplikasi Flask
CMD ["python", "app.py"]
