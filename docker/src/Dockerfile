# SBOMPY - default container (stable Debian slim)
FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1     PYTHONUNBUFFERED=1

# sudo  
RUN apt-get update && apt-get install -y --no-install-recommends vim nano ca-certificates curl  && rm -rf /var/lib/apt/lists/*

# ---- install syft (pinned) ----
ARG SYFT_VERSION=v1.6.0
RUN curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh   | sh -s -- -b /usr/local/bin ${SYFT_VERSION}

# ---- install trivy (pinned) ----
ARG TRIVY_VERSION=0.69.2
RUN curl -sSfL https://github.com/aquasecurity/trivy/releases/download/v${TRIVY_VERSION}/trivy_${TRIVY_VERSION}_Linux-64bit.tar.gz   | tar -xz -C /usr/local/bin trivy

# Create a non-root user
RUN useradd -m -u 10001 -s /usr/sbin/nologin sbompy


WORKDIR /app
COPY pyproject.toml README.md LICENSE /app/
COPY src/ /app/src/

RUN pip install --no-cache-dir -U pip  && pip install --no-cache-dir .

RUN mkdir -p /data/sboms /data/cache  && chown -R 10001:10001 /data /app

USER 10001:10001

EXPOSE 8080
CMD ["sbompy"]
