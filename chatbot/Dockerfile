FROM rasa/rasa:3.5.4

ARG HOST_IP

WORKDIR /app
USER root
COPY . /app

RUN rasa train

RUN sed -i "s,http://localhost:5055/webhook,http://$HOST_IP:8080/chatbot-actions,g" /app/endpoints.yml

EXPOSE 5005

CMD ["run", "-m", "/app/models", "--enable-api", "--cors", "*", "--debug", "--endpoints", "/app/endpoints.yml", "--log-file", "out.log", "--debug"]