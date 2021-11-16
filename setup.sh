#!/bin/sh
FLASK_APP=navigator_engine/app.py pipenv run flask navigator-engine load-graph
