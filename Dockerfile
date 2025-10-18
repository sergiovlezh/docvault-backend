FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /workspace

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*

RUN python -m pip install --upgrade pip setuptools wheel pip-tools

COPY requirements.txt ./requirements.txt

RUN pip-sync ./requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "src/manage.py", "runserver", "0.0.0.0:8000"]
