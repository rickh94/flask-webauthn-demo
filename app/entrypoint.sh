#!/usr/bin/env bash
flask db upgrade && waitress-serve --host 0.0.0.0 --port 5000 app:app