## SKP Game

### some commands

```
# start gunicorn
gunicorn -w 3 --threads 2 -b :8080 skp:app # no use in production
gunicorn -c gunicorn.py skp:app --daemon # no use in production

# start with supervisord
supervisord -c /root/dev/tencent-flask/example/supervisor.conf
```

### api doc
https://docs.qq.com/sheet/xxxxxxxx
