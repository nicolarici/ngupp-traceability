# Prototype of file traceability for the Court of Brescia

## Conda environment management


Create conda env for developing
```console
conda create -n ngupp python=3.8 flask flask-wtf email_validator flask-sqlalchemy flask-migrate flask-login qrcode pillow flask-bootstrap flask-mail pyjwt -c conda-forge
```


## Useful commands:

Connect to the server in tunneling to be able to open the site from the local browser
```console
ssh -L localhost:5000:localhost:5000 user@10.20.255.201
```



Start the Flask server:
```console
conda activate ngupp
flask run
```


## Database
Initialization
```console
flask db init
```

After all schema modification (modification to models.py)
```console
flask db migrate -m "message"
flask db upgrade
```

# Mail-server
Fake email server start
```console
python -m smtpd -c DebuggingServer -n localhost:1025
```


