geohealthcheck
==============

Service Status Checker for OGC Web Services

```bash
virtualenv geohealthcheck && cd $_
. bin/activate
git clone https://github.com/geopython/geohealthcheck.git
cd geohealthcheck
pip install -r requirements.txt
vi instance/config.py  # edit SQLALCHEMY_DATABASE_URI
# setup database
python geohealthcheck/models.py create
# drop database
python geohealthcheck/models.py drop

# start server (default is 0.0.0.0:8000)
python geohealthcheck/app.py  
# start server on another port
python geohealthcheck/app.py 0.0.0.0:8881
# start server on another IP
python geohealthcheck/app.py 192.168.0.105:8001
```


users
- view all services
- view service

admin
- drop db
- create db
- add service
- delete service
- run health check (cron or interactive)
