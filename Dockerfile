FROM python:3.11.4

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY bot.py /app/

CMD ["python", "bot.py"]