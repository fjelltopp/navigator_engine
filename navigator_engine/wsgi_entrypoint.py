"""Entry point module for WSGI

This is used when running the app using a WSGI server such as uWSGI
"""
print("Monkey patching the standard library...")
from gevent import monkey
monkey.patch_all()

print("Creating app...")
from navigator_engine.app import create_app
app = create_app()
