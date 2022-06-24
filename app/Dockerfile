FROM python:3.10

RUN apt-get update
RUN apt-get install -y wait-for-it
RUN pip install poetry
RUN pip install waitress
ADD app/pyproject.toml .
ADD app/poetry.lock .
RUN poetry export -o requirements.txt
RUN pip install -r requirements.txt
COPY app /app
WORKDIR /app

CMD sh /app/entrypoint.sh
