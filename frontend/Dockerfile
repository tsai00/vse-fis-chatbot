FROM ubuntu
RUN apt-get update && \
    apt-get install -y  \
    apache2 apache2-utils

ARG HOST_IP
WORKDIR /var/www/html
COPY . .

RUN sed -i 's,http://localhost:5005/webhooks/rest/webhook,http://$HOST_IP:8080/chatbot,g' /var/www/html/static/js/constants.js
RUN sed -i 's,http://localhost:5055/webhook,http://$HOST_IP:8080/chatbot-actions,g' /var/www/html/static/js/constants.js

EXPOSE 80

CMD ["apache2ctl", "-D", "FOREGROUND"]