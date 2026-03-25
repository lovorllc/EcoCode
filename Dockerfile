FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies
COPY requirements.txt /app/
RUN apt-get update \
	&& apt-get install -y --no-install-recommends build-essential gcc libffi-dev libssl-dev \
	&& rm -rf /var/lib/apt/lists/* \
	&& pip install --upgrade pip==26.0.1 \
	&& pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . /app

EXPOSE 8000

CMD ["python", "run_server.py"]
