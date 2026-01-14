FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/code

RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /code

RUN apt-get update && apt-get install -y \
    gcc \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /code/
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

COPY . /code/

RUN mkdir -p /code/staticfiles /code/mediafiles

# Copy and make entrypoint script executable
COPY scripts/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Change ownership
RUN chown -R appuser:appuser /code
USER appuser

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
