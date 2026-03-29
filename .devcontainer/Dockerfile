FROM mcr.microsoft.com/devcontainers/python:1-3.13-bookworm

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl git just nodejs npm \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv
