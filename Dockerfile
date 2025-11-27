FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# create non-root user
#RUN useradd -ms /bin/bash appuser
#USER appuser

EXPOSE 8000

CMD ["gunicorn", "app:create_app()", "-w", "4", "-b", "0.0.0.0:8000", "--timeout", "120"]
