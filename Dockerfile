FROM python:3.14-slim
WORKDIR /app
EXPOSE 8050
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "main.py"]