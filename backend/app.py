import sys, os, time
import glob, json, argparse
import socket, webbrowser
import wsgiref.simple_server
from bottle import *
import serial
from serial_manager import SerialManager
from flash import flash_upload
import linuxcnc
import re

APPNAME = "lasaurapp"
VERSION = "v12.06h"
COMPANY_NAME = "com.nortd.labs"
SERIAL_PORT = None
BITSPERSECOND = 9600
NETWORK_PORT = 4444
CONFIG_FILE = "lasaurapp.conf"
COOKIE_KEY = 'secret_key_jkn23489hsdf'

if os.name == 'nt': #sys.platform == 'win32': 
    GUESS_PREFIX = "Arduino"   
elif os.name == 'posix':
    GUESS_PREFIX = "tty.usbmodem"   
else:
    GUESS_PREFIX = "no prefix"    

c = linuxcnc.command()
s = linuxcnc.stat()

def resources_dir():
    """This is to be used with all relative file access.
       _MEIPASS is a special location for data files when creating
       standalone, single file python apps with pyInstaller.
       Standalone is created by calling from 'other' directory:
       python pyinstaller/pyinstaller.py --onefile app.spec
    """
    if hasattr(sys, "_MEIPASS"):
        return sys._MEIPASS
    else:
        # root is one up from this file
        return os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../'))
        
        
def storage_dir():
    directory = ""
    if sys.platform == 'darwin':
        # from AppKit import NSSearchPathForDirectoriesInDomains
        # # NSApplicationSupportDirectory = 14
        # # NSUserDomainMask = 1
        # # True for expanding the tilde into a fully qualified path
        # appdata = path.join(NSSearchPathForDirectoriesInDomains(14, 1, True)[0], APPNAME)
        directory = os.path.join(os.path.expanduser('~'), 'Library', 'Application Support', COMPANY_NAME, APPNAME)
    elif sys.platform == 'win32':
        directory = os.path.join(os.path.expandvars('%APPDATA%'), COMPANY_NAME, APPNAME)
    else:
        directory = os.path.join(os.path.expanduser('~'), "." + APPNAME)
        
    if not os.path.exists(directory):
        os.makedirs(directory)
        
    return directory
        



def run_with_callback(host):
    """ Start a wsgiref server instance with control over the main loop.
        This is a function that I derived from the bottle.py run()
    """
    handler = default_app()
    server = wsgiref.simple_server.make_server('0.0.0.0', NETWORK_PORT, handler)
    server.timeout = 0.01
    server.quiet = True
    print "-----------------------------------------------------------------------------"
    print "Bottle server starting up ..."
    print "Serial is set to %d bps" % BITSPERSECOND
    print "Point your browser to: "    
    print "http://%s:%d/      (local)" % ('127.0.0.1', NETWORK_PORT)    
    if host == '':
        print "http://%s:%d/   (public)" % (socket.gethostbyname(socket.gethostname()), NETWORK_PORT)
    print "Use Ctrl-C to quit."
    print "-----------------------------------------------------------------------------"    
    print
#    try:
#        webbrowser.open_new_tab('http://127.0.0.1:'+str(NETWORK_PORT))
#    except webbrowser.Error:
#        print "Cannot open Webbrowser, please do so manually."
    sys.stdout.flush()  # make sure everything gets flushed
    while 1:
        try:
            SerialManager.send_queue_as_ready()
            server.handle_request()
        except KeyboardInterrupt:
            break
    print "\nShutting down..."
    SerialManager.close()

        

@route('/hello')
def hello_handler():
    return "Hello World!!"

@route('/longtest')
def longtest_handler():
    fp = open("longtest.ngc")
    for line in fp:
        SerialManager.queue_for_sending(line)
    return "Longtest queued."
    


@route('/css/:path#.+#')
def static_css_handler(path):
    return static_file(path, root=os.path.join(resources_dir(), 'frontend/css'))
    
@route('/js/:path#.+#')
def static_js_handler(path):
    p = re.compile('gauss', re.IGNORECASE)
    if not len(p.findall(request.url)):
        return static_file(path, root=os.path.join(resources_dir(), 'frontend/js'))
    
@route('/img/:path#.+#')
def static_img_handler(path):
    return static_file(path, root=os.path.join(resources_dir(), 'frontend/img'))
    

### LIBRARY

@route('/library/get/:path#.+#')
def static_library_handler(path):
    return static_file(path, root=os.path.join(resources_dir(), 'library'), mimetype='text/plain')
    
@route('/library/list')
def library_list_handler():
    # return a json list of file names
    file_list = []
    cwd_temp = os.getcwd()
    try:
        os.chdir(os.path.join(resources_dir(), 'library'))
        file_list = glob.glob('*')
    finally:
        os.chdir(cwd_temp)
    return json.dumps(file_list)



### QUEUE

def encode_filename(name):
    str(time.time()) + '-' + base64.urlsafe_b64encode(name)
    
def decode_filename(name):
    index = name.find('-')
    return base64.urlsafe_b64decode(name[index+1:])
    

@route('/queue/get/:name#.+#')
def static_queue_handler(name): 
    return static_file(name, root=storage_dir(), mimetype='text/plain')

@route('/queue/list')
def library_list_handler():
    # base64.urlsafe_b64encode()
    # base64.urlsafe_b64decode()
    # return a json list of file names
    files = []
    cwd_temp = os.getcwd()
    try:
        os.chdir(storage_dir())
        files = filter(os.path.isfile, glob.glob("*"))
        files.sort(key=lambda x: os.path.getmtime(x))
    finally:
        os.chdir(cwd_temp)
    return json.dumps(files)
    
@route('/queue/save', method='POST')
def queue_save_handler():
    ret = '0'
    if 'gcode_name' in request.forms and 'gcode_program' in request.forms:
        name = request.forms.get('gcode_name')
        gcode_program = request.forms.get('gcode_program')
        filename = os.path.abspath(os.path.join(storage_dir(), name.strip('/\\')))
        if os.path.exists(filename) or os.path.exists(filename+'.starred'):
            return "file_exists"
        try:
            fp = open(filename, 'w')
            fp.write(gcode_program)
            print "file saved: " + filename
            ret = '1'
        finally:
            fp.close()
    else:
        print "error: save failed, invalid POST request"
    return ret

@route('/queue/rm/:name')
def queue_rm_handler(name):
    # delete gcode item, on success return '1'
    ret = '0'
    filename = os.path.abspath(os.path.join(storage_dir(), name.strip('/\\')))
    if filename.startswith(storage_dir()):
        if os.path.exists(filename):
            try:
                os.remove(filename);
                print "file deleted: " + filename
                ret = '1'
            finally:
                pass
    return ret   
    
@route('/queue/star/:name')
def queue_star_handler(name):
    ret = '0'
    filename = os.path.abspath(os.path.join(storage_dir(), name.strip('/\\')))
    if filename.startswith(storage_dir()):
        if os.path.exists(filename):
            os.rename(filename, filename + '.starred')
            ret = '1'
    return ret    

@route('/queue/unstar/:name')
def queue_unstar_handler(name):
    ret = '0'
    filename = os.path.abspath(os.path.join(storage_dir(), name.strip('/\\')))
    if filename.startswith(storage_dir()):
        if os.path.exists(filename + '.starred'):
            os.rename(filename + '.starred', filename)
            ret = '1'
    return ret 

    

@route('/')
@route('/index.html')
@route('/app.html')
def default_handler():
    p = re.compile('gauss', re.IGNORECASE)
    if not len(p.findall(request.url)): 
        return static_file('app.html', root=os.path.join(resources_dir(), 'frontend') )

@route('/canvas')
def canvas_handler():
    return static_file('testCanvas.html', root=os.path.join(resources_dir(), 'frontend'))    

@route('/serial/:connect')
def serial_handler(connect):
    return "1"

@route('/flash_firmware')
def flash_firmware_handler():
    if SerialManager.is_connected():
        SerialManager.close()
    global SERIAL_PORT, GUESS_PREFIX
    if not SERIAL_PORT:
        SERIAL_PORT = SerialManager.match_device(GUESS_PREFIX)        
    flash_upload(SERIAL_PORT, resources_dir())
    return '<h2>flashing finished!</h2> Check Log window for possible errors.<br><a href="/">return</a>'

# @route('/gcode/:gcode_line')
# def gcode_handler(gcode_line):
#     if SerialManager.is_connected():    
#         print gcode_line
#         SerialManager.queue_for_sending(gcode_line)
#         return "Queued for sending."
#     else:
#         return ""

@route('/gcode', method='POST')
def gcode_submit_handler():
    gcode_program = request.forms.get('gcode_program')
    try:
        gcode = open("/tmp/gcode.ngc", 'w')
        gcode.write(gcode_program)
        gcode.write('\n')
        return "Sent to AXIS."
    except:
        return ""
    '''try:
      c.abort()
      c.wait_complete()
      c.reset_interpreter()
      c.wait_complete()
      c.state(linuxcnc.STATE_ESTOP_RESET)
      c.wait_complete()
      c.state(linuxcnc.STATE_ON)
      c.wait_complete()
      c.mode(linuxcnc.MODE_MANUAL)
      c.wait_complete()
      c.home(0)
      c.wait_complete()
      c.home(1)
      c.wait_complete()
      while s.homed[0:2] != (1,1):
        s.poll()
      c.mode(linuxcnc.MODE_AUTO)
      c.wait_complete()
      c.program_open('/tmp/gcode.ngc')
      c.wait_complete()
      c.auto(linuxcnc.AUTO_RUN, 0)
      c.wait_complete()
    except:
       print "Unexpected error:", sys.exc_info()[0].strerror
    return 1 
    if gcode_program and SerialManager.is_connected():
        lines = gcode_program.split('\n')
        print "Adding to queue %s lines" % len(lines)
        for line in lines:
            SerialManager.queue_for_sending(line)
        return "Queued for sending."
    else:
        return ""'''

@route('/queue_pct_done')
def queue_pct_done_handler():
    return SerialManager.get_queue_percentage_done()


# @route('/svg_upload', method='POST')
# # file echo - used as a fall back for browser not supporting the file API
# def svg_upload():
#     data = request.files.get('data')
#     if data.file:
#         raw = data.file.read() # This is dangerous for big files
#         filename = data.filename
#         print "You uploaded %s (%d bytes)." % (filename, len(raw))
#         return raw
#     return "You missed a field."



# def check_user_credentials(username, password):
#     return username in allowed and allowed[username] == password
#     
# @route('/login')
# def login():
#     username = request.forms.get('username')
#     password = request.forms.get('password')
#     if check_user_credentials(username, password):
#         response.set_cookie("account", username, secret=COOKIE_KEY)
#         return "Welcome %s! You are now logged in." % username
#     else:
#         return "Login failed."
# 
# @route('/logout')
# def login():
#     username = request.forms.get('username')
#     password = request.forms.get('password')
#     if check_user_credentials(username, password):
#         response.delete_cookie("account", username, secret=COOKIE_KEY)
#         return "Welcome %s! You are now logged out." % username
#     else:
#         return "Already logged out."  
  


### Setup Argument Parser
argparser = argparse.ArgumentParser(description='Run LasaurApp.', prog='lasaurapp')
argparser.add_argument('port', metavar='serial_port', nargs='?', default=False,
                    help='serial port to the Lasersaur')
argparser.add_argument('-v', '--version', action='version', version='%(prog)s ' + VERSION)
argparser.add_argument('-p', '--public', dest='host_on_all_interfaces', action='store_true',
                    default=False, help='bind to all network devices (default: bind to 127.0.0.1)')
argparser.add_argument('-f', '--flash', dest='build_and_flash', action='store_true',
                    default=False, help='flash Arduino with LasaurGrbl firmware')
argparser.add_argument('-l', '--list', dest='list_serial_devices', action='store_true',
                    default=False, help='list all serial devices currently connected')
argparser.add_argument('-d', '--debug', dest='debug', action='store_true',
                    default=False, help='print more verbose for debugging')
argparser.add_argument('-m', '--match', dest='match',
                    default=GUESS_PREFIX, help='match serial device with this string')                                        
args = argparser.parse_args()



def run_helper():
    if args.debug:
        debug(True)
        if hasattr(sys, "_MEIPASS"):
            print "Data root is: " + sys._MEIPASS             
        print "Persistent storage root is: " + storage_dir()
    if args.build_and_flash:
        flash_upload(SERIAL_PORT, resources_dir())
    else:
        if args.host_on_all_interfaces:
            run_with_callback('')
        else:
            run_with_callback('127.0.0.1')    
            

print "LasaurApp " + VERSION
if args.list_serial_devices:
    SerialManager.list_devices()
else:
    if args.port:
        # (1) get the serial device from the argument list
        SERIAL_PORT = args.port
        print "Using serial device '"+ SERIAL_PORT +"' from command line."
    else:
        # (2) get the serial device from the config file        
        if os.path.isfile(CONFIG_FILE):
            fp = open(CONFIG_FILE)
            line = fp.readline().strip()
            if len(line) > 3:
                SERIAL_PORT = line
                print "Using serial device '"+ SERIAL_PORT +"' from '" + CONFIG_FILE + "'."

    if not SERIAL_PORT:
        if args.match:
            GUESS_PREFIX = args.match
            SERIAL_PORT = SerialManager.match_device(GUESS_PREFIX)
            if SERIAL_PORT:
                print "Using serial device '"+ str(SERIAL_PORT)
                print "(first device to match: " + args.match + ")"            
        else:
            SERIAL_PORT = SerialManager.match_device(GUESS_PREFIX)
            if SERIAL_PORT:
                print "Using serial device '"+ str(SERIAL_PORT) +"' by best guess."
    
    if not SERIAL_PORT:
        print "-----------------------------------------------------------------------------"
        print "WARNING: LasaurApp doesn't know what serial device to connect to!"
        print "Make sure the Lasersaur hardware is connectd to the USB interface."
        print "-----------------------------------------------------------------------------"      
    
    # run
    run_helper()     

        


