FROM python:3.13-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_SYSTEM_PYTHON=1

WORKDIR /app

RUN rm -rf /etc/apt/sources.list.d/* && \
  echo "\
    deb https://mirrors.ustc.edu.cn/debian bookworm main contrib non-free non-free-firmware\n\
    deb https://mirrors.ustc.edu.cn/debian bookworm-updates main contrib non-free non-free-firmware\n\
    deb https://mirrors.ustc.edu.cn/debian-security bookworm-security main contrib non-free non-free-firmware\n\
    " > /etc/apt/sources.list

RUN apt-get clean && apt-get update --fix-missing && \
    apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

COPY . .

RUN uv sync --frozen

RUN mkdir -p /app/workspace

CMD ["uv", "run", "devmate", "chat"]
