FROM python:3.12-slim


ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app


RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*


COPY server/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt


COPY server/ /app/server/
COPY Encryption/ /app/Encryption/
COPY blockchain/ /app/blockchain/


RUN chmod +x /app/server/start.sh


EXPOSE 8000


RUN mkdir -p /app/server/dbdata


WORKDIR /app/server


CMD ["/bin/bash", "start.sh"]
