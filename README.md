# Getting started

This is RESTful API which will allow you to interact with Paladeum blockchain.

# Run

```
$ gunicorn app:app --worker-class eventlet -w 1 --bind 0.0.0.0:4321 --reload
```
