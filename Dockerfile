FROM fjelltopp/python-fjelltopp-base:3.9

COPY ./ /var/www/navigator_engine
WORKDIR /var/www/navigator_engine
RUN mkdir .venv && pipenv sync

EXPOSE 5001
