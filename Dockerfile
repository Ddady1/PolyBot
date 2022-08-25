FROM python:3.8.12-slim-buster

COPY ./ code

WORKDIR /code

COPY requirements.txt .

RUN pip install -r requirements.txt

CMD ["python3", "bot.py"