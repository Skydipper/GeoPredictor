from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello_world(name='world'):
    """A hello world func"""
    return f"Hello {name}"