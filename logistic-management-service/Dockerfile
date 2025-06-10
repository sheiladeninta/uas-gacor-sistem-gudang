# Gunakan image Python 3.10 sebagai base image
FROM python:3.10

# Set direktori kerja di dalam container
WORKDIR /app

# Salin file dari host ke dalam container
COPY . /app

# Install dependensi
RUN pip install --no-cache-dir -r requirements.txt

# Set variabel environment untuk Flask
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0

# Expose port yang digunakan oleh Flask
EXPOSE 5000

# Jalankan aplikasi Flask
CMD ["flask", "run"]
