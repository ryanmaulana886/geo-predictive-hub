# 1. Menggunakan base image Python resmi yang stabil
FROM python:3.10-slim

# 2. Install dependensi sistem yang wajib ada untuk GeoPandas & FPDF2
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libgdal-dev \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 3. Atur folder kerja di dalam server
WORKDIR /app

# 4. Copy file requirements dan install library Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy seluruh sisa kodingan aplikasi ke dalam server
COPY . .

# 6. Buka jalur akses port standar Streamlit
EXPOSE 8501

# 7. Perintah untuk menjalankan Streamlit saat server aktif
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]