FROM python:3.10

RUN apt-get update
RUN apt-get install -y wait-for-it
RUN pip install poetry
RUN pip install waitress
ADD . /app
WORKDIR /app
RUN poetry export -o requirements.txt
RUN pip install -r requirements.txt

CMD sh -c ./entrypoint.sh