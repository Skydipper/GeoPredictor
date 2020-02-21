#!/bin/bash
set -e

case "$1" in
    develop)
        echo "Running Development Server"
        exec python main.py
        ;;
    start)
        echo "Running Production Server"
        exec python main.py
        ;;
    test)
        echo "Test"
        ;;
    *)
        exec "$@"
esac
