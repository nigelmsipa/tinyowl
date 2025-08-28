#!/bin/bash
# Simple launcher script for the theology query tool

cd "$(dirname "$0")"
source venv/bin/activate
python simple_query.py "$@"