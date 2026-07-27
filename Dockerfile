# Imagem do pipeline (extract/transform/quality/load/aggregate/views).
# Debian bookworm explicito: e a distribuicao para a qual a Microsoft
# documenta e testa o pacote msodbcsql18 (driver ODBC 18 for SQL Server).
FROM python:3.14-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# Dependencias de sistema + driver ODBC da Microsoft (necessario para pyodbc).
# Ver: https://learn.microsoft.com/sql/connect/odbc/linux-mac/installing-the-microsoft-odbc-driver-for-sql-server
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
        gnupg2 \
        unixodbc \
        unixodbc-dev \
        gcc \
        g++ \
    && curl -sSL -o /usr/share/keyrings/microsoft-prod.gpg https://packages.microsoft.com/keys/microsoft.asc \
    && curl -sSL https://packages.microsoft.com/config/debian/12/prod.list -o /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y --no-install-recommends msodbcsql18 mssql-tools18 \
    && apt-get purge -y gnupg2 curl && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

ENV PATH="$PATH:/opt/mssql-tools18/bin"

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ src/
COPY sql/ sql/
COPY alembic/ alembic/
COPY alembic.ini ./
COPY docker/entrypoint-pipeline.sh /usr/local/bin/entrypoint-pipeline.sh
RUN chmod +x /usr/local/bin/entrypoint-pipeline.sh

# data/ e montado como volume (ver docker-compose.yml) - criamos apenas a
# estrutura minima para o primeiro start funcionar antes do mount.
RUN mkdir -p data/raw data/trusted data/analytics data/rejected

ENTRYPOINT ["/usr/local/bin/entrypoint-pipeline.sh"]
CMD ["python", "-m", "src.main", "--stage", "all"]
