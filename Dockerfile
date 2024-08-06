FROM chetan1111/botasaurus:latest

ENV PYTHONUNBUFFERED=1

COPY requirements.txt .

RUN python -m pip install -r requirements.txt

RUN mkdir app
WORKDIR /app
COPY . /app

EXPOSE 8765

RUN python run.py install

CMD ["sh", "-c", "python run.py && uvicorn api_on_top:scrapping_api --host 0.0.0.0 --port 8765"]
