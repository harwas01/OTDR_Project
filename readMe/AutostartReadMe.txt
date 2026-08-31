# this is only used when running Flask in development mode
# otherwise gunicorn is started as a service and gunicorn invokes app

mkdir -p ~/.config/autostart
cd ~/.config/autostart
nano myscript.desktop
	[Desktop Entry]
	Type=Application
	Name=OTDR App
	Exec=sudo python3 /home/pi/Documents/OTDR_Project/app.py
	
	For desktop application (not used) :
	Exec=sudo env DISPLAY=$DISPLAY XAUTHORITY=$XAUTHORITY python3 /home/pi/Documents/OTDR_Project/app.py
