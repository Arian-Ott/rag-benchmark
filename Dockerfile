FROM python:3.12-alpine3.20
LABEL authors="arian.ott"
COPY requirements.txt .
RUN pip3 install --no-cache-dir --upgrade -r requirements.txt

COPY . .
RUN rm requirements.txt

EXPOSE 6969

CMD ["uvicorn", "app.main:app", "--host=0.0.0.0", "--port=6969","--workers=4"]
