import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your_strong_secret_key'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://user:password@db:5432/mydatabase'
    SQLALCHEMY_TRACK_MODIFICATIONS = False