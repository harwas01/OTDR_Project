#procedure for setting up with nginx and gunicorn
#must use the venv environment
python -m venv .venv
source .venv/bin/activate

#then install at /home/Documents/OTDR_Project with the (.venv) prompt
pip install flask
pip install flask_socketio
pip install flask_login
pip install smbus2
pip install pyotdr
pip install pyserial
pip install gevent
pip install packaging
pip install matplotlib

#starting gunicorn from the command line - wporks with gevent
#done from /home/Documents/OTDR_Project
# to determine if it's running: sudo ps aux | grep gunicorn
./.venv/bin/gunicorn -w 1 -k gevent --bind 0.0.0.0:8000 app:app

# setting it up as a service
# sudo nano /etc/systemd/system/gunicorn.service

[Unit]
Description=Gunicorn instance to serve my Python app
After=network.target

[Service]
User=pi
Group=pi
WorkingDirectory=/home/pi/Documents/OTDR_Project
ExecStart=/home/pi/Documents/OTDR_Project/.venv/bin/gunicorn --w 1 -k gevent --bind 0.0.0.0:8000 app:app
Restart=always

[Install]
WantedBy=multi-user.target

# sudo systemctl start gunicorn - starts it
# sudo systemctl enable gunicorn - starts on bootup
