FROM rasa/rasa-sdk:3.5.0

USER root
RUN apt-get update -qq && \
    apt-get install -y python3-icu pkg-config libicu-dev build-essential wget && \
    wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list' && \
    apt-get update && \
    apt-get install google-chrome-stable && \
    apt-get clean

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
RUN pip install --no-binary=:pyicu: pyicu   # Due to the errors with installing pyicu on linux

COPY . .

EXPOSE 5055