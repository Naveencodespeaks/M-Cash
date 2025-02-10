FROM python:3.8.10-slim

ENV PYTHONUNBUFFERED=1
ENV PORT=8000
#ENV DATABASE_URL=mysql+pymysql://remittance:remittance2024@10.11.12.111/remittance_test

WORKDIR /app

RUN apt-get update && apt-get install -y \
    pkg-config \
    gcc \
    libmariadb-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY requirements_latest.txt .
RUN pip install --no-cache-dir -r requirements_latest.txt

#COPY pyproject.toml poetry.lock* /app/

# Install pip and Poetry
#RUN pip install --upgrade pip && \
    #pip install poetry==1.8.3

#RUN poetry install --no-dev --no-interaction --no-ansi

COPY . /app/
#COPY alembic.sh /app/
#RUN chmod +x /app/alembic.sh

EXPOSE 8000
#CMD ["/app/alembic.sh"]
CMD ["uvicorn", "application:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]