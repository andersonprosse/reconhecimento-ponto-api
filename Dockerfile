FROM python:3.12-slim

# Correção dos avisos de variáveis
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Correção do pacote do OpenCV para o Linux mais recente (libgl1)
RUN apt-get update --fix-missing && \
    apt-get install -y --no-install-recommends \
    default-libmysqlclient-dev \
    build-essential \
    pkg-config \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Instala as dependências do Python
COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copia o projeto inteiro
COPY . /app/

# Expondo a porta correta para o EasyPanel
EXPOSE 8000

# Coleta os arquivos estáticos para o painel de admin funcionar
RUN python manage.py collectstatic --noinput

# Servidor de Produção Robusto com Migração Automática
CMD bash -c "python manage.py makemigrations && python manage.py migrate && gunicorn --bind 0.0.0.0:8000 gestao.wsgi:application"
