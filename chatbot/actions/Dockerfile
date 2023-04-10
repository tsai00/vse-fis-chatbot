FROM rasa/rasa-sdk:3.5.0

USER root
RUN apt-get update -qq && \
    apt-get install -y python3-icu pkg-config libicu-dev python3-dev build-essential && \
    apt-get clean

WORKDIR /app
COPY requirements.txt requirements.txt
COPY . .

RUN pip install -r requirements.txt
RUN pip install --no-binary=:pyicu: pyicu   # Due to the errors with installing pyicu on linux

EXPOSE 5055

USER 1001