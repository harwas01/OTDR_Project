from flask import Flask, render_template, request, redirect, url_for, flash, abort
from flask_socketio import SocketIO
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from smbus2 import SMBus, i2c_msg
from enum import Enum

from OTDRService import *

import json
import os
import serial
import atexit
import shutil

#added by me for windows operation
BAUD_RATE = 9600
if sys.platform == "win32":
    print("Running on Windows")
    SERIAL_PORT = 'COM6'        # random windows assignment
    CONFIG_FILE_NAME = ".\\config.json" 
    LOCAL_CONFIG_FILE_NAME  = ".\\localConfig.json"
    RESULTS_FILE_PATH = ".\\results"
    LASTRUN_FILENAME = ".\\lastRun\\trace.txt"
    from waitress import serve
elif sys.platform == "linux":
    print("Running on Linux")
    CONFIG_FILE_NAME = "/home/pi/Documents/OTDR_Project/config.json"                   # requires full path for autostartcd 
    LOCAL_CONFIG_FILE_NAME = "/home/pi/Documents/OTDR_Project/localConfig.json"        # requires full path for autostartcd 
    RESULTS_FILE_PATH = "/home/pi/Documents/OTDR_Project/results"
    LASTRUN_FILENAME = "/home/pi/Documents/OTDR_Project/lastRun/trace.txt"
    SERIAL_PORT = '/dev/ttyUSB0' 
RESULTS_FILE_NAME = 'TestResult.csv'

lastIpAddr  = "0.0.0.0"
lastPort    = "0"   
lastMask    = "0.0.0.0"
lastGateway = "0.0.0.0"
lastDate = "0"
channelSelect = 0
graphPath = ""

I2CBUSADDR = 1
TLC_ADDR = 0x60

class ledMap(Enum):
    reg1 = 2
    reg2 = 3
    reg3 = 4
    reg4 = 5
    reg5 = 9   # layout error
    reg6 = 8   # layout error
    reg7 = 7   # layout error
    reg8 = 6   # layout error
    reg9 = 10
    reg10 = 11
    reg11 = 12
    reg12 = 13

    
app = Flask(__name__)
# The secret key is mandatory to encrypt session cookies
app.config['SECRET_KEY'] = 'goFoton'
app.config['LOGIN_DISABLED'] = False
app.config['TESTING'] = False
#socketio = SocketIO(app, cors_allowed_origins="http://127.0.0.1:5000")      # localhost
socketio = SocketIO(app, cors_allowed_origins="*")

''' should work this way - but Flask doesn't exit gracefully on python errors
    so port must be initialized and closed each time and costs 2 seconds 
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=15)  # device takes 15 seconds to move
except Exception as e:
    print(f"Serial Error: {e}")
    ser = None
    
def close_serial():
    if ser is not None:
        ser.close()
        
atexit.register(close_serial)

'''

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Redirects unauthorized users to the login route

# A minimal User class required by Flask-Login
class User(UserMixin):
    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash

# Mock Database: Hardcoded user dictionary (In production, load this from a real DB)
# Password used here: "admin"
USERS_DB = {
    "1": User(
        id="1", 
        username="admin", 
        password_hash=generate_password_hash("admin")
    ),
    "2": User(
        id="2", 
        username="user", 
        password_hash=generate_password_hash("user")
    )
}

def writeReg(reg , data):
    status = False
    try:
        with SMBus(I2CBUSADDR) as bus:
            #print("Bus ok")
            bus.write_byte_data(TLC_ADDR, reg , data)
        status = True
    except:
        status = False
    return status

def updateLeds():
    if channelSelect != 0:
        for index, member in enumerate(ledMap):
            if str(index + 1) == channelSelect:
                val = 255
            else:
                val = 0
            #print(f"Reg, Value, Index = {member.value}, {val}, {index}")
            if writeReg(member.value , val) is not True:
                print(f"Unable to set TLC59116 Reg {ledEnum[i].value}")      

def clearLeds():              
    for i in range(12):
        reg = i + 0x02
        if writeReg(reg, 0) is not True:
            print(f"Unable to set TLC59116 Reg {reg}")    

def initTLC59116():
    # MODE1
    if writeReg(0x00, 0x00) is not True:
        print("Unable to set Mode1 of TLC59116")

    # MODE2
    if writeReg(0x01, 0x04) is not True:
        print("Unable to set Mode2 of TLC59116")

    # LED0～15 to be PWM
    if writeReg(0x14, 0xAA) is not True:
        print("Unable to set Reg 20 of TLC59116")
    if writeReg(0x15, 0xAA) is not True:
        print("Unable to set Reg 21 of TLC59116")
    if writeReg(0x16, 0xAA) is not True:
        print("Unable to set Reg 22 of TLC59116")
    if writeReg(0x17, 0xAA) is not True:
        print("Unable to set Reg 23 of TLC59116")

    # LED OFF
    clearLeds()


# initialization of OTDR Device parameters
def initOTDR():
    if os.path.exists(CONFIG_FILE_NAME):
        with open(CONFIG_FILE_NAME, "r", encoding="utf-8") as f:
            config = json.load(f)
            f.close()
            ipAddr  = config["NET"][0]
            port    = config["NET"][1]
            client = CLientSocketConnectToOtdr(ipAddr, int(port))
            if client is not None:
                #ALA
                mode = config["ALA"][0]
                setting = config["ALA"][1]
                if True != setOtdrSamplingTime(client, int(mode), int(setting)):               
                    print("Could not set ALA during initilization")
                #AVG   
                avg = config["AVG"][0]
                if True != setOtdrAverageMode(client, int(avg)):
                    print("Could not set AVG") 
                #STP    
                distanceMode   = config["STP"][0]                   
                distance       = config["STP"][1]                   
                pulseWidthMode = config["STP"][2]                   
                pulseWidth     = config["STP"][3]                   
                sampleMode     = config["STP"][4]                   
                if True != setOtdrSTP(client, int(distanceMode), int(distance), int(pulseWidthMode), int(pulseWidth),int(sampleMode)):        
                    print("Could not set STP during initilization") 
                #THS    
                depletionThreshold = config["THS"][0]
                if True != setOtdrEventLossThresholdofFiber(client, float(depletionThreshold)):
                    print("Could not set THS during initilization") 
                #THR2
                reflexThreshold = config["THR2"][0]
                if True != setOtdrEventReflectThresholdofFiber(client, float(reflexThreshold)):
                    print("Could not set THR2 during initilization")                     
                #THF
                terminalThreshold = config["THF"][0]
                if True != setOtdrEndThresholdofFiber(client, float(terminalThreshold)):
                    print("Could not set THF during initilization") 
                #IOR
                refractiveIndex = config["IOR"][0]
                if True != setOtdrRefractiveIndexofFiber(client, float(refractiveIndex)):
                    print("Could not set IOR during initilization")                     
                #BSL2
                scatteringCoefficient = config["BSL2"][0]
                if True != setOtdrScatteringCoefofFiber(client, float(scatteringCoefficient)):
                    print("Could not set BSL2 during initilization") 

# hardware initialization
initTLC59116()
initOTDR()

              

@login_manager.user_loader
def load_user(user_id):
    # This callback reloads the user object from the session ID
    return USERS_DB.get(user_id)

@app.route('/')
def home():
    return redirect(url_for('login'))
    
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Search for the user in our mock database
        user = next((u for u in USERS_DB.values() if u.username == username), None)
        
        # Verify the user exists and the cryptographically hashed password matches
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'error')
            
    return render_template('login.html')

@app.route('/setup')
@login_required
def setup_page():
    json_string = ""
    global lastIpAddr, lastPort, lastMask, lastGateway, lastDate
    if os.path.exists(CONFIG_FILE_NAME):
        with open(CONFIG_FILE_NAME, "r", encoding="utf-8") as f:
            config = json.load(f)
            json_string = json.dumps(config)
            if("NET" in config):
                lastIpAddr  = config["NET"][0]
                lastPort    = config["NET"][1]  
                lastMask    = config["NET"][2]
                lastGateway = config["NET"][3]
                print("lastIpAddr", lastIpAddr)
            if("DATE2" in config):
                lastDate = "DATE2 "
                lastDate += config["DATE2"][0]
                lastDate += ", "
                lastDate += config["DATE2"][1]
                lastDate += ", "                
                lastDate += config["DATE2"][2]
                lastDate += ", "                
                lastDate += config["DATE2"][3]
                lastDate += ", "                
                lastDate += config["DATE2"][4]
                lastDate += ", 00"
                print("lastDate", lastDate)
    return render_template('setup.html', data=json_string)
    
@app.route('/test')
@login_required
def test_page():
    json_string = ""
    if os.path.exists(CONFIG_FILE_NAME):
        with open(CONFIG_FILE_NAME, "r", encoding="utf-8") as f:
            config = json.load(f)
            json_string = json.dumps(config)
    json_local_string = ""
    if os.path.exists(LOCAL_CONFIG_FILE_NAME):
        with open(LOCAL_CONFIG_FILE_NAME, "r", encoding="utf-8") as f:
            local_config = json.load(f)
            json_local_string = json.dumps(local_config)
    return render_template('test.html', data=json_string, localData=json_local_string)       
 
    
@app.route('/admin')
@login_required
def admin_page(): 
    user_name = current_user.username
    if user_name != 'admin':
        abort(403)  # Returns an HTTP 403 Forbidden error page
    json_string = ""
    json_local_string = ""
    if os.path.exists(CONFIG_FILE_NAME):
        with open(CONFIG_FILE_NAME, "r", encoding="utf-8") as f:
            config = json.load(f)
            json_string = json.dumps(config)
    if os.path.exists(LOCAL_CONFIG_FILE_NAME):
        with open(LOCAL_CONFIG_FILE_NAME, "r", encoding="utf-8") as f:
            local_config = json.load(f)
            json_local_string = json.dumps(local_config)
    return render_template('admin.html', data=json_string, localData=json_local_string)
    
@app.route('/gotoDashboard')
def gotoDashboard():
    print("gotoDashboard")
    return redirect(url_for('dashboard'))
    
@app.route('/gotoTest')
def gotoTest():
    print("gotoTest")
    return redirect(url_for('test_page'))
   

@app.route('/gotoSetup')
def gotoSetup():
    print("gotoSetup")
    return redirect(url_for('setup_page'))

@app.route('/dashboard')
@login_required  # Protects this route from logged-out users
def dashboard():
    return render_template('dashboard.html')
    
    
@socketio.on('refresh_test_page')
def refresh_test_page():
    print("refresh_test_page")
    if os.path.exists(graphPath):
        sendResults(graphPath)
    if channelSelect != 0:
        updateLeds()
        socketio.emit('device_data', {'source': 'serial', 'payload': str(channelSelect)})
        
@socketio.on('update_graph')
def update_graph(message):
    print("update_graph called")
    filePath = message.get('file')
    if filePath.exists():
        sendResults(filePath)     

@socketio.on('update_json')
def update_json(message):
    print("update_json called")
    key  = message.get('cmd')
    arg1 = message.get('arg1')
    arg2 = message.get('arg2')    
    arg3 = message.get('arg3')    
    arg4 = message.get('arg4')    
    arg5 = message.get('arg5')   
    arg6 = message.get('arg6')

    data = {}
    new_data = {}
    if arg6 != '':
        new_data = {key: [arg1, arg2, arg3, arg4, arg5, arg6]}
    elif arg5 != '':
        new_data = {key: [arg1, arg2, arg3, arg4, arg5]}
    elif arg4 != '':
        new_data = {key: [arg1, arg2, arg3, arg4]}
    elif arg3 != '':
        new_data = {key: [arg1, arg2, arg3]}
    elif arg2 != '':
        new_data = {key: [arg1, arg2]}
    else:
        new_data = {key: [arg1],}
        
    #print(new_data)
        
    if os.path.exists(CONFIG_FILE_NAME):
        with open(CONFIG_FILE_NAME, "r", encoding="utf-8") as f:
            data = json.load(f)
            data.update(new_data)
            f.close()
    else:
        data = new_data       

    with open(CONFIG_FILE_NAME, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
        f.close()
        
    result = {"status": "success", "payload": "Here is your data"}
    socketio.emit('response_data', result)
    
@socketio.on('update_local_json')
def update_local_json(message):
    print("update_local_json called")
    key  = message.get('cmd')
    arg = message.get('arg')
    
    new_data = {key: arg}
    
    if os.path.exists(LOCAL_CONFIG_FILE_NAME):
        with open(LOCAL_CONFIG_FILE_NAME, "r", encoding="utf-8") as f:
            data = json.load(f)
            data.update(new_data)
            f.close()
    else:
        data = new_data       

    with open(LOCAL_CONFIG_FILE_NAME, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
        f.close()
        
    result = {"status": "success", "payload": "Here is your local data"}
    socketio.emit('response_local_data', result)

@socketio.on('update_OTDR')
def update_OTDR(message):
    print("update_OTDR called")
    global lastIpAddr, lastPort, lastMask, lastGateway, lastDate
    if os.path.exists(CONFIG_FILE_NAME):
        with open(CONFIG_FILE_NAME, "r", encoding="utf-8") as f:
            config = json.load(f)
            f.close()
            print(config)
            ipAddr  = config["NET"][0]
            port    = config["NET"][1]
            mask    = config["NET"][2]
            gateway = config["NET"][3]
            tempIpAddr = ipAddr
            tempPort = port
            tempMask = mask
            tempGateway = gateway
            netChange = False
            if((lastIpAddr == "0.0.0.0") and (lastPort == "0")):
                netChange = True
            else:
                if(ipAddr != lastIpAddr): 
                    tempIpAddr = lastIpAddr
                    netChange = True
                if(port != lastPort):
                    tempPort = lastPort
                    netChange = True
                if(mask != lastMask): 
                    netChange = True
                if(gateway != lastGateway):
                    netChange = True            
            #print("ipAddr", ipAddr)  
            #print("port", port)  
            #print("tempIpAddr", tempIpAddr)  
            #print("tempPort", tempPort)
            client = CLientSocketConnectToOtdr(tempIpAddr, int(tempPort))
            if client is not None:
                lastIpAddr = ipAddr
                lastPort = port
                lastMask = mask
                lastGateway = gateway
                #print("client_connected to", tempIpAddr, lastPort)
                #ALA
                mode = config["ALA"][0]
                setting = config["ALA"][1]
                if True != setOtdrSamplingTime(client, int(mode), int(setting)):               
                    print("Could not set ALA")
                #AVG   
                avg = config["AVG"][0]
                if True != setOtdrAverageMode(client, int(avg)):
                    print("Could not set AVG") 
                #STP    
                distanceMode   = config["STP"][0]                   
                distance       = config["STP"][1]                   
                pulseWidthMode = config["STP"][2]                   
                pulseWidth     = config["STP"][3]                   
                sampleMode     = config["STP"][4]  
                if(int(distance) < 500):            # crashes
                    distance = "500"
                if True != setOtdrSTP(client, int(distanceMode), int(distance), int(pulseWidthMode), int(pulseWidth),int(sampleMode)):        
                    print("Could not set STP") 
                #THS    
                depletionThreshold = config["THS"][0]
                if True != setOtdrEventLossThresholdofFiber(client, float(depletionThreshold)):
                    print("Could not set THS") 
                #THR2
                reflexThreshold = config["THR2"][0]
                if True != setOtdrEventReflectThresholdofFiber(client, float(reflexThreshold)):
                    print("Could not set THR2")                     
                #THF
                terminalThreshold = config["THF"][0]
                if True != setOtdrEndThresholdofFiber(client, float(terminalThreshold)):
                    print("Could not set THF") 
                #IOR
                refractiveIndex = config["IOR"][0]
                if True != setOtdrRefractiveIndexofFiber(client, float(refractiveIndex)):
                    print("Could not set IOR")                     
                #BSL2
                scatteringCoefficient = config["BSL2"][0]
                if True != setOtdrScatteringCoefofFiber(client, float(scatteringCoefficient)):
                    print("Could not set BSL2") 
                #DATE2
                setDate = "DATE2 "
                setDate += config["DATE2"][0]
                setDate += ", "
                setDate += config["DATE2"][1]
                setDate += ", "                
                setDate += config["DATE2"][2]
                setDate += ", "                
                setDate += config["DATE2"][3]
                setDate += ", "                
                setDate += config["DATE2"][4]
                setDate += ", 00"
                if(lastDate != setDate):
                    print("date change detected")
                    if True != setOtdrDate(client, setDate):
                        print("Could not set DATE2") 
                lastDate = setDate
                if(netChange):      # cannot change net every time - causes problems, probably requires reboot
                    Ip      = config["NET"][0]
                    Port    = int(config["NET"][1])              
                    Mask    = config["NET"][2]             
                    Gateway = config["NET"][3]
                    print("net change detected", Ip, Port, Mask, Gateway)
                    if True != setOtdrNet(client,Ip,Port,Mask,Gateway):
                        print("Could not set NET")       
                    else :   
                        print("NET successful")  

                    
                    
                

def read_data_in_chunks(file_path, chunk_size):
    chunk = []
    with open(file_path, 'r') as f:
        reader = csv.reader(f, delimiter='\t')
        next(reader)    # 2 header rows
        next(reader)
        for row in reader:
            if not row:     # Ignore blank rows
                continue
                # chunk.append({'x': float(row[0]), 'y': float(row[1])})
            chunk.append({'x': row[0], 'y': row[1]})
            if len(chunk) >= chunk_size:
                yield chunk
                chunk = []
        if chunk:           # Yield any remaining rows
            yield chunk
            
def sendResults(tracePath):
    print("sendResults called")  
    #for chunk in read_data_in_chunks(LASTRUN_FILENAME, chunk_size=32768):
    for chunk in read_data_in_chunks(tracePath, 1024): # must go over in 1 chunk so javascript pesists minY maxY etc... 32768
        #print(chunk)
        socketio.emit('data_chunk', {'points': chunk})
        socketio.sleep(0.1) # Yield to event loop to prevent buffer bloat   
    socketio.emit('data_complete')
    
def limitResults():
    print("limitResults called")  
    if not os.path.exists(RESULTS_FILE_PATH):
        print("Results Directory Not Found")
        return
        
    subdirs = []
    with os.scandir(RESULTS_FILE_PATH) as entries:
        for entry in entries:
            if entry.is_dir():
                subdirs.append(entry.path)
                
    subdirs.sort(key=lambda d: os.path.getmtime(d), reverse=False)
    print(subdirs)
    print(len(subdirs))
    
    excess_count = len(subdirs) - 10
    if excess_count <= 0:
        print("No subdirectories to delete.")
        return

    # Delete the oldest ones
    for subdir in subdirs[:excess_count]:
        try:
            mtime = os.path.getmtime(subdir)
            shutil.rmtree(subdir)
            print(f"Deleted: {subdir} (Last modified: {time.ctime(mtime)})")
        except Exception as e:
            print(f"Failed to delete {subdir}: {e}")        

@socketio.on('start_measure')
def startMeasureOTDR():
    print("startMeasureOTDR called")
    global graphPath
    with open(CONFIG_FILE_NAME, "r", encoding="utf-8") as f:
        config = json.load(f)
        f.close()
        ipAddr = config["NET"][0]
        port   = config["NET"][1]    
        client = CLientSocketConnectToOtdr(ipAddr, int(port))
        if client is not None:
            AverageMode = getOtdrAverageMode(client)
            Lambda_nm = getOtdrWaveLength(client)
            DistanceMode, Distance_m, PulseWidthMode, PulseWidth_ns, SampleMode = getOtdrSTP(client)
            if PulseWidthMode == '1':
                PulseWidth_ns = '0'
            if DistanceMode == '1':
                Distance_m = '0'
            mode, MeasureTime_s = getOtdrSamplingTime(client)
            EndThreshold = getOtdrEndThresholdofFiber(client)
            NonReflectThreshold = 0
            nGIR = 1.4670
            flg, tracePath = StartMeasure(client,'OPWILL', int(AverageMode), int(Lambda_nm), int(Distance_m), int(PulseWidth_ns), int(MeasureTime_s), nGIR, float(EndThreshold), NonReflectThreshold, RESULTS_FILE_PATH, RESULTS_FILE_NAME)
            print(tracePath) 
            print(flg)            
            if flg:
                sendResults(tracePath)
                graphPath = tracePath
            else:
                graphPath = ""
            limitResults()
            
@socketio.on('stop_measure')
def stopMeasureOTDR():
    print("stopMeasureOTDR called")
    with open(CONFIG_FILE_NAME, "r", encoding="utf-8") as f:
        config = json.load(f)
        f.close()
        ipAddr = config["NET"][0]
        port   = config["NET"][1]    
        client = CLientSocketConnectToOtdr(ipAddr, int(port))
        if client is not None:
            StopMeasure(client)

@socketio.on('send_command')
def send_command(message):
    print("send_command")
    global channelSelect
    target = message.get('target')
    command = message.get('command')
    if target == 'serial':
        try:
            clearLeds()
            ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=15)     # should not be done here
            time.sleep(2)                                               # waste of time
            cmd = f"{command}".encode('utf-8')
            ser.write(cmd)
            byte_data = ser.readline()
            ser.close()                                                 # in case python bombs out
            string_data = byte_data.decode("utf-8").strip()
            #print(string_data)
            socketio.emit('device_data', {'source': 'serial', 'payload': string_data})
            channelSelect = string_data
            updateLeds()
        except Exception as e:
            print(f"Serial Error: {e}")
    elif target == 'network':
        new_string = command + "\r\n"
        request = (new_string.encode('utf-8'))
        print(request)
        try:
            client_socket.sendall(request)
        except socket.timeout:
            print("Socket send timed out")
        except socket.error as e:
            print(f"Socket send error occurred: {e}")
            
        socketio.emit('device_data', {'source': 'send', 'payload': request.decode("utf-8")})

        response = ""
        try:
            response = client_socket.recv(4096)
        except socket.timeout:
            print("Socket receive timed out")
        except socket.error as e:
            print(f"Socket receive error occurred: {e}")
        
        socketio.emit('device_data', {'source': 'recv', 'payload': response.decode("utf-8")})
            
@socketio.on('do_reset')
def do_reset(message):
    print("do_reset called")
    with open(CONFIG_FILE_NAME, "r", encoding="utf-8") as f:
        config = json.load(f)
        f.close()
        ipAddr = config["NET"][0]
        port   = config["NET"][1]    
        client = CLientSocketConnectToOtdr(ipAddr, int(port))    
        if client is not None:
            ret = OtdrDeviceReset(client)
            print(ret)
        
@socketio.on('otdr_mode')
def otdr_mode(message):
    print("otdr_mode called")
    key  = message.get('cmd')       # unused here
    arg1 = message.get('arg1')
    with open(CONFIG_FILE_NAME, "r", encoding="utf-8") as f:
        config = json.load(f)
        f.close()
        ipAddr = config["NET"][0]
        port   = config["NET"][1]    
        client = CLientSocketConnectToOtdr(ipAddr, int(port))    
        if client is not None:
            ret = setOtdrMode(client, arg1)
            print(ret)
                    
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have successfully logged out.', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
#    app.run(debug=True)                                # pc
    app.run(host='0.0.0.0', port=5000, debug=True)      # raspberry pi
        