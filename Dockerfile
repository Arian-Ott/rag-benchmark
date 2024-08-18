FROM python:3.12-slim-bullseye
LABEL authors="arian.ott"
RUN apt update && apt upgrade -y

COPY . .
RUN pip3 install -r requirements.txt
RUN rm requirements.txt
EXPOSE 6969

CMD ["uvicorn", "app.main:app", "--host=0.0.0.0", "--port=6969"]
