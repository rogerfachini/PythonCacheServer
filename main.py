#Python HTTP server for caching thw page content
#Written by Roger Fachini

#--------------------------------===Config===--------------------------------
ip = 'localhost'
port = 5042
liveURL = 'http://www.modkit.com/vex/editor'

sourceDir  = 'modkitSource'
projectDir = 'Projects'
logDir     = 'logs'
dumpURLs   = logDir+'/listAllURL.txt'

downloadFilesOnStartup = True

#The console will only print an event to stdout if it's priority is in the list.
""" 
logLevel = [0,    #Debug <white text>
            1,    #Info <blue text>
            2,    #Warning <yellow text>
            3,    #Error <red text>
            4,    #Crash Log <dark red text>
            ]
"""
logLevel = [0,1,2,3,4]

#--------------------------------===Constants===--------------------------------
contentTypes = { 'htm':'text/html',
                 'css':'text/css',
                 'png':'image/png',
                 'ico':'image/ico',
                  'js':'application/javascript',
                'json':'text/javascript',
                 'gif':'image/gif',
                 'ttf':'application/x-font-ttf',
                 'svg':'image/svg+xml',
                'woff':'application/font-woff' }

binaryFiles = ['png','ico','gif'] 
logStrings = ['[ DEBUG ]','[ INFO ] ','[WARNING]','[ ERROR ]','[ CRASH ]']
logColors =  [ 0x0f,       0x09,      0x0e,       0x0c,         0xc0   ]
#---------------------------------===Imports===---------------------------------
import cgi    
import ctypes
import calendar, time, datetime
import urllib 
import os, sys 
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer 

#-------------------------------===Class Defs===-------------------------------
class Logger:
    def __init__(self):
        self.std_out_handle = ctypes.windll.kernel32.GetStdHandle(-11)
        with open(dumpURLs,"a+") as file:
            self.existingURLs = file.readlines()

        self.createLogFile()

    def setTermColor(self,color):
        bool = ctypes.windll.kernel32.SetConsoleTextAttribute(self.std_out_handle, color)
        return bool

    def createLogFile(self):
        self.logFile = '%s/%s.log' % (logDir,
                                      str(datetime.datetime.now()).split('.')[0]
                                                                  .replace(':','.'))
        t = open(self.logFile,"a+")
        print '[PRE-LOG] Created Log File:',self.logFile
        t.close()

    def LogToFile(self,format, *args, **keywords):
            if keywords.has_key('level'): level = keywords['level']             
            else: level = 1
                
            string = ("%s %s\n" % (logStrings[level], format%args))

            with open(self.logFile,"a+") as file:
                file.write(string)

            self.setTermColor(logColors[level])
            if level in logLevel:
                print string,

    def logURL(self,URL):
        if URL+'\n' in self.existingURLs:
            return
        with open(dumpURLs, "a") as file:
            file.write(URL+'\n')
            self.existingURLs.append(URL+'\n')

            log.LogToFile('%s: %s','Logged a new path:',URL ,level=0)

    def _logExistingFiles(self):                                                                                                  
        r = []                                                                                                            
        subdirs = [x[0] for x in os.walk(sourceDir)]                                                                            
        for subdir in subdirs:                                                                                            
            files = os.walk(subdir).next()[2]                                                                             
            if (len(files) > 0):                                                                                          
                for file in files:                                                                                        
                    r.append((subdir + "\\" + file).replace('\\','/').replace(sourceDir,''))                                                                         
        for f in r:
            self.logURL(f)
            
class Server:
    def __init__(self, ip, port):
        """
        *Called on object creation*
        Creates a HTTPServer object with a custom handler and starts handling requests
        """
        if downloadFilesOnStartup:
            for file in log.existingURLs:
                f = file.replace('\n','').replace(sourceDir,'').replace('\\','/')
                self.serverSteal(f)
        log.LogToFile('%s','Starting creation of server instance')
        self.server = HTTPServer((ip, port), self._customHandler) 
        log.LogToFile('%s http://%s:%s','Server Instance started on:', ip, str(port))

    def ServeForever(self):
        log.LogToFile('%s','Now serving HTTP Requests!')
        self.server.serve_forever()  

    class _customHandler(BaseHTTPRequestHandler):
        """
        *Extends the BaseHTTPRequestHandler class*
        Defines custom handling subroutines for the server
        """
        def do_GET(self):
            """
            *Called on a GET request*
            """
            path = self.path                                             

            if path == '/':                                              
                if not os.path.isfile(sourceDir+'/index.htm'):           
                    urllib.urlretrieve (liveURL, 
                                        sourceDir+'/index.htm')         
                f = open(sourceDir+'/index.htm')                         
                self.send_response(200)                                  
                self.send_header('Content-type','text/html')             
                self.end_headers()                                       
                self.wfile.write(f.read())                               
                f.close()                                                

            elif 'getProjects' in path:                                  
                #TODO: Reverse engineer how this transaction occurs                                                         
                self.log_message(' %s',                                  
                                 'Unable to handle getProjects request!',
                                 level=2) 

                self.send_response(500)
            
            else:                                                      
                s.serverSteal(path)                                
                self.send_response(200)                              
                fileType = path.split('.')[-1]  
                             
                try:
                    self.send_header('Content-type',contentTypes[fileType]) 
                except KeyError:                                        
                    self.send_header('Content-type',contentTypes['htm']) 
                    self.log_message(' %s [%s]',                       
                                     'Unknown content-type for file:',
                                     path,
                                     level=2)                     
                self.end_headers()   
                #TODO: Should we open ALL files in binary-read mode?                                  
                if fileType in binaryFiles:                             
                    f = open(sourceDir+path, 'rb')                         
                else: 
                    f = open(sourceDir+path)                                
                self.wfile.write(f.read())                             
                f.close()                                              

        def do_POST(self):
            path = self.path
            temp = path.split('/')
            name = temp[-1].split('.')[:-1][0]
            type = temp[-1].split('.')[-1]
            ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
            if ctype == 'multipart/form-data':
                postvars = cgi.parse_multipart(self.rfile, pdict)
            elif ctype == 'application/x-www-form-urlencoded':
                length = int(self.headers.getheader('content-length'))
                postvars = cgi.parse_qs(self.rfile.read(length), keep_blank_values=1)
            else:
                return
            s.writeFile(projectDir,name,'.'+type,str(postvars)) 
            self.send_response(200)
        
        def log_error(self, format, *args):
            log.LogToFile(format, *args,level=4)

        def log_message(self,format, *args, **keywords):
            log.LogToFile(format,*args,**keywords)

    def writeFile(self,folder,name,type,data):
        """
        Creates a file in <folder> with <name><type> and writes <data> to it.
        If the file exists, it will not overwrite it. 
        Syntax for overwrite protection:
            <name>~save~<version><type>
            name.type
            name~save~0.type
            name~save~1.type

        """
        #TODO: Clean this up if possible
        folder += '/'                                 
        file = folder+name+type                        
        if os.path.isfile(file):                  
            fileList = []                         
            for file in os.listdir(folder):              
                if file.endswith(type) and name in file: 
                    fileList.append(file)             
            fileList.sort()                           
            filePart = fileList[-1].split('.')[0]     
            
            if '~save~' in filePart:                 
                version = int(filePart.split('~')[-1]) 
                filePart = name+'~save~'+str(version+1) 
            else:                                       
                filePart += '~save~0'                   

            file = folder+filePart+type                 
        
        f = open(file,'a')                          
        f.write(data) 
        log.LogToFile('Wrote %s bytes to file: (%s)',len(str(data)),file,level=0)                              
        f.close()                                  
    
    def serverSteal(self,URL):
            
        """
        *Called for each file requessted by the application*
        Creates a cached copy of the file in a local directory from the server if it does not already exist locally
        """        
        log.logURL(URL)

        if os.path.isfile(sourceDir+URL):      
            return                                
        directory = (URL).split('/')[:-1]       
        directory = '/'.join(directory)+'/'       

        if not os.path.exists(sourceDir+directory):
            os.makedirs(sourceDir+directory)      
        
        try:
            log.LogToFile(' %s %s',                    
                          'Downloading:',
                          liveURL+URL,
                          level=0) 

            urllib.urlretrieve(liveURL+URL, sourceDir+URL)
        except BaseException as er:          
            log.LogToFile(' %s %s',               
                          'ERROR DOWNLOADING FILE:',
                          er,
                          level=3)

if __name__ == '__main__':  

    sys.stdout.write('[PRE-LOG] Checking if main folders exist..')
    if not os.path.exists(sourceDir):
        print '\n[PRE-LOG] Webpage source directory does not exist! Creating...'
        os.makedirs(sourceDir)

    if not os.path.exists(logDir):
        print '\n[PRE-LOG] Log file directory does not exist! Creating...'
        os.makedirs(logDir)

    if not os.path.exists(projectDir):
        print '\n[PRE-LOG] Project save directory does not exist! Creating...'
        os.makedirs(projectDir)
    print '..Done!'

    log = Logger()         
    log._logExistingFiles()

    s = Server(ip,port)    
    s.ServeForever()       

