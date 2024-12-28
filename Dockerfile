FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=stock_market.settings \
    PORT=80 \
    PATH="/home/appuser/.local/bin:$PATH"

WORKDIR /app

ENV DEBUG=False

# Install system dependencies, TA-Lib, and Miniconda
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libxml2-dev \
        libxslt-dev \
        wget \
        curl \
        ca-certificates \
    && wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz \
    && tar -xvzf ta-lib-0.4.0-src.tar.gz \
    && cd ta-lib/ \
    && ./configure --prefix=/usr \
    && make \
    && make install \
    && cd .. \
    && rm -rf ta-lib ta-lib-0.4.0-src.tar.gz \
    && wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh \
    && bash miniconda.sh -b -p /opt/conda \
    && rm miniconda.sh \
    && /opt/conda/bin/conda install -y -c conda-forge ta-lib \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /opt/conda/pkgs/*

ENV LD_LIBRARY_PATH=/usr/lib:$LD_LIBRARY_PATH

# Create and switch to non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Install Python dependencies
COPY --chown=appuser:appuser requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Copy project files
COPY --chown=appuser:appuser . .

# Create necessary directories and set permissions
RUN mkdir -p staticfiles media \
    && chmod -R 755 staticfiles media

# Remove the migrate command from here since it should run after environment is set up
RUN python manage.py collectstatic --noinput
EXPOSE $PORT

CMD gunicorn --config gunicorn-cfg.py stock_market.wsgi:application