FROM rasa/rasa:3.5.4

WORKDIR /app
USER root
COPY . /app

RUN rasa train

EXPOSE 5005

USER 1001

CMD ["run", "-m", "/app/models", "--enable-api", "--cors", "*", "--debug"]