FROM python:3.10-slim

# 1. Correção dos avisos (usando o sinal de =)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# 2. Correção do Erro 100 (Adicionando fix-missing, pkg-config e limpeza)
RUN apt-get update --fix-missing && \
    apt-get install -y --no-install-recommends \
    default-libmysqlclient-dev \
    build-essential \
    pkg-config \
    libgl1-mesa-glx \
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

# 3. Servidor de Produção Robusto
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "gestao.wsgi:application"]
