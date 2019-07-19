#!/bin/bash
set -e

case "$1" in
    develop)
        echo "Running Development Server"
        exec python Validator/main.py
        ;;
    test)
        echo "Test"
        ;;
    *)
        exec "$@"
esac
