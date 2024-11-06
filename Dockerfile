FROM --platform=$BUILDPLATFORM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=stock_market.settings \
    PORT=8000 \
    PATH="/home/appuser/.local/bin:$PATH"

WORKDIR /app

ENV DEBUG=False

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        chromium \
        chromium-driver \
        build-essential \
        chromium-l10n \
        fonts-liberation \
        libasound2 \
        libatk-bridge2.0-0 \
        libatk1.0-0 \
        libatspi2.0-0 \
        libcups2 \
        libdbus-1-3 \
        libdrm2 \
        libgbm1 \
        libgtk-3-0 \
        libnspr4 \
        libnss3 \
        libxcomposite1 \
        libxdamage1 \
        libxfixes3 \
        libxrandr2 \
        xdg-utils \
        libxml2-dev \
        libxslt-dev \
    && rm -rf /var/lib/apt/lists/*

# Create and switch to non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Install Python dependencies
COPY --chown=appuser:appuser requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt \
    && pip install --user --no-cache-dir gunicorn

# Copy project files
COPY --chown=appuser:appuser . .

# Create necessary directories and set permissions
RUN mkdir -p staticfiles media \
    && chmod -R 755 staticfiles media

# Collect static files
RUN python manage.py collectstatic --noinput
RUN python manage.py migrate

EXPOSE $PORT

# Use full path to gunicorn
CMD ["gunicorn", "--config", "gunicorn-cfg.py", "stock_market.wsgi:application"]