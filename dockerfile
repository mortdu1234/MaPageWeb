FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 25555

CMD ["gunicorn", "--bind", "0.0.0.0:25555", "app:create_app()"]