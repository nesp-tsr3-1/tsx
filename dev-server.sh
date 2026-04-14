#!/bin/bash

FLASK_DEBUG=1 FLASK_APP=tsx/api/api.py python -m flask run -p 5001 -h 0.0.0.0
