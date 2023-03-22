FROM ghcr.io/fjelltopp/fjelltopp-base-images/python-fjelltopp-base:master

COPY ./ /var/www/navigator_engine
WORKDIR /var/www/navigator_engine
RUN mkdir .venv && pipenv sync

EXPOSE 5001
