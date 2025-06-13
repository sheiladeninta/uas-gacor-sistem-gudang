# Gunakan image Python
FROM python:3.8-slim

# Set working directory
WORKDIR /app

# Salin requirements.txt dan install dependensi
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Salin semua file ke dalam container
COPY . /app/

# Jalankan aplikasi
CMD ["python", "app.py"]
