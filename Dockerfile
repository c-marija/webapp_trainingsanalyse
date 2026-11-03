FROM python:3.13-slim

WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY README.md ./
COPY src ./src

RUN pip install --no-cache-dir uv \
    && uv sync --frozen --no-dev

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/src"

EXPOSE 8000

# Beim Start zuerst fehlende Tabellen und den Anfangsbestand anlegen (löscht
# nichts), dann Gunicorn starten.
#  * PORT setzt Render; ohne Angabe 8000.
#  * --timeout 180: Gemini braucht bis zu 150 Sekunden (ki_service.py),
#    Gunicorn bricht standardmässig nach 30 Sekunden ab.
#  * --threads 4: Während eine Anfrage auf Gemini wartet, können andere
#    Anfragen weiterlaufen. Mit nur einem Faden wäre die ganze Anwendung so
#    lange blockiert.
CMD ["sh", "-c", "flask --app app setup-db && exec gunicorn --bind 0.0.0.0:${PORT:-8000} --timeout 180 --threads 4 app:app"]
