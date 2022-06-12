FROM python:3.8.12-slim-buster
COPY ./ Polybot
WORKDIR /Polybot
COPY requirements.txt .
RUN pip install -r requirements.txt


CMD ["python3", "bot.py"]