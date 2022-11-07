# Prototype of file traceability for the Court of Brescia

## Conda environment management


Create conda env for developing
```console
conda create -n ngupp python=3.8 flask flask-wtf email_validator flask-sqlalchemy flask-migrate flask-login qrcode pillow flask-bootstrap flask-mail pyjwt -c conda-forge
```


## Useful commands:

### Developmente

Connect to the server in tunneling to be able to open the site from the local browser and start the web site and the fake email server
```console
ssh -L localhost:5000:localhost:5000 user@10.20.255.201

conda activate ngupp
cd ngupp-traceability/
nohup python email_server.py > /home/user/email_server.log &
flask --debug run


```

### Production
Connect to the server and start the web site and the fake email server:
```console
ssh -i "aws_key.pem" ubuntu@ec2-34-244-14-112.eu-west-1.compute.amazonaws.com

sudo su
conda activate ngupp
cd ngupp-traceability/
nohup python email_server.py > /home/ubuntu/email_server.log &
flask run --host=0.0.0.0 --port=80
```


