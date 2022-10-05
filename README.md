# Prototype of file traceability for the Court of Brescia

## Conda environment management


Create conda env for developing
```console
conda create -n ngupp python=3.8 flask flask-wtf email_validator flask-sqlalchemy flask-migrate
```

## Useful commands:

Connect to the server in tunneling to be able to open the site from the local browser
```console
ssh -L localhost:5000:localhost:5000 [username]@[ip-server]
```



Start the Flask server:
```console
conda activate ngupp
flask --debug run
```


