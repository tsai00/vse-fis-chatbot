FROM rasa/rasa:3.5.4

WORKDIR /app
USER root
COPY . /app

RUN sed -i 's/localhost:5055/chatbot_actions:5055/g' endpoints.yml

RUN rasa train

EXPOSE 5005

CMD ["run", "-m", "/app/models", "--enable-api", "--cors", "*", "--debug", "--endpoints", "endpoints.yml", "--log-file", "out.log", "--debug"]