FROM python:3.10-slim

# Evita que o Python gere arquivos .pyc
ENV PYTHONDONTWRITEBYTECODE 1
# Evita que o output do Python seja armazenado em buffer
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# Instala as dependências do sistema necessárias (MySQL e OpenCV)
RUN apt-get update \
    && apt-get install -y default-libmysqlclient-dev build-essential libgl1-mesa-glx libglib2.0-0 \
    && apt-get clean

# Instala as dependências do Python
COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copia o projeto inteiro
COPY . /app/

# Expondo a porta
EXPOSE 8000

# Comando para iniciar a aplicação usando Gunicorn ou o servidor nativo
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
