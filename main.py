#Python HTTP server for caching webpage page content
#Written by Roger Fachini

#--------------------------------===Config===--------------------------------
ip = 'localhost'  #web server IP, change to the internal network IP. 
port = 5042       #web server port, must be unique on the network adapter

#the base URL to get cached content from
liveURL = 'http://www.modkit.com/vex/editor' 

#The subdirectory to store the cached files in
sourceDir  = 'modkitSource'

#The subdir to store project save files in
projectDir = 'Projects'

#The subdir to store log files and the URL cache file in
logDir     = 'logs'
#The file and subdir to store the URL cache file
dumpURLs   = logDir+'/listAllURL.txt'

#When this is true, any missing files will be downloaded when the server starts
downloadFilesOnStartup = True

#--------------------------------===Constants===--------------------------------
#Lookup dict of file types and MIME content headers
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

#File types that should be opened in binary read mode
binaryFiles = ['png','ico','gif'] 

#GET paths that need to be redirected to a specific URL
overrideURLs = {'/favicon.ico':'http://www.modkit.com/favicon.ico'}

#---------------------------------===Imports===---------------------------------
import cgi, ast, json  #Modules for string parsing and data formatting    
import ctypes          #Access to low-level system calls and OS API features
import urllib          #Module for downloading content from a URL
import os, sys         #Modules for mid-level system operations and filesystem operations
import logging         #Module for pretty-ifying the console and logging to a file
import calendar, time, datetime #Modules for timestamps
from warnings import filterwarnings, catch_warnings            #Should cause any runtime exceptions to become non-fatal and instead print to STDERR
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer  #Python's built-in bare-bones HTTP server

#-------------------------------===Class Defs===-------------------------------
    
class Server:
    def __init__(self, ip, port):
        """
        *Called on object creation*
        Does basic server initalization, reads the URL cache file, and downloads any missing sources
        """
        #Create a new logging instance for the server
        self.logging = logging.getLogger('server.root')  

        #Read the file containing all the known URLs that we need to cache
        with open(dumpURLs,"a+") as file:   
                self.existingURLs = file.readlines()
                self.logging.debug('Read URL dump file, %i total entries.'%len(self.existingURLs))

        #When it is enabled, attempt to download all files before server load. 
        #This is really only needed when initially populating the source directory
        if downloadFilesOnStartup:
            for file in self.existingURLs: #Iterate through known URLs
                #Format file name into a usable URL
                f = file.replace('\n','').replace(sourceDir,'').replace('\\','/') 
                #Attempt to download the file
                self.serverSteal(f)
        
        #Create a new local instance of the save file handler. 
        self.save = self.SaveHandler()

        self.logging.info('Starting creation of server instance')
        #Create a new HTTP server object, bind it to the ip and port, and assign it 
        #our custom handler class
        self.server = HTTPServer((ip, port), self._customHandler) 
        self.logging.info('Server Instance started on: http://%s:%s', ip, str(port))     
    def ServeForever(self):
        """
        WARNING: This is a BLOCKING operation!
        Starts the HTTP server
        """
        self.logging.info('Now serving HTTP Requests!')
        
        #Instruct the HTTP server to serve indefinently
        self.server.serve_forever()  

    def logURL(self,URL):
        """
        *!Called for ALL URL REQUESTS TO THE SERVER!*
        Write a URL to the URL cache file if it has not been called before.
        """
        #Check if the URl exists already in the cache file, and exit if it is
        if URL in self.existingURLs or URL+'\n' in self.existingURLs:
            return
       
        with open(dumpURLs, "a") as file:          
            file.write('\n'+URL) #Open the cache file in write-append mode and write a newline char and the URL
            self.existingURLs.append(URL+'\n') #Add the URl to the local list of URLs
            logging.debug('Logged a new path: %s',URL) 
    def _logExistingFiles(self):    
        """
        Iterate through the current cache directory and log the existing files as URLs
        """                                                                                              
        r = [] #Initalize an empty list to put URLs in                                                                                                             
        subdirs = [x[0] for x in os.walk(sourceDir)] #Create an object with the directory tree of the cache directory                                                                           
        for subdir in subdirs:                       #Iterate through the subdirectories in the tree                                                                                           
            files = os.walk(subdir).next()[2]        #Advance the iteration of the tree                                                                      
            if (len(files) > 0):                     #Make sure the directory is not empty                                                                                           
                for file in files:                   #Iterate through each file in each subdir        
                    #Convert the directory string into an acceptable URL and append it to the list                                                                                    
                    r.append((subdir+"\\"+file).replace('\\','/').replace(sourceDir,'')) 

        #Iterate through the list of file URLs and add them to the cache file if they do not exist                                                                          
        for f in r:
            self.logURL(f)
    def serverSteal(self,URL):            
        """
        *Called for each file requessted by the application*
        Creates a cached copy of the file in a local directory from the server if it does not already exist locally
        """        
        self.logURL(URL) #Add the requested URL to the url cache file (will exit early if the line already exists)

        #Exit prematurely if the requested file already exists
        if os.path.isfile(sourceDir+URL):      
            return     
        
        #Do some string formatting to remove the filename and get just the directory                           
        directory = (URL).split('/')[:-1]       
        directory = '/'.join(directory)+'/'       

        #Create the directory if it does not exist (urlretrieve raises an exception if the directory does not exist)
        if not os.path.exists(sourceDir+directory):
            os.makedirs(sourceDir+directory)      
        
        #Download the file, and log an error if one occurs
        try:
            self.logging.debug('Downloading: %s', liveURL+URL) 
            urllib.urlretrieve(liveURL+URL, sourceDir+URL)
        except BaseException as er:          
            self.logging.warn('ERROR DOWNLOADING FILE: %s', er)

    class _customHandler(BaseHTTPRequestHandler):
        """
        *Extends the BaseHTTPRequestHandler class*
        Defines custom handling subroutines for the server. 
        Responds to GET and POST requests unique to ModKit. 
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
                data = f.read().replace('var preloggedInUser',
                                        'var preloggedInUser="tnter1234@gmail.com"')                                
                self.wfile.write(data)                               
                f.close()                                                

            elif 'getProjects' in path:   
                self.send_response(200)

                self.send_header('Content-Type','application/json')
                self.end_headers()
                s.save._checkProjectData()

                json_obj = json.dumps(s.save.projectData)
                u = unicode(str(json_obj), "utf-8")

                self.wfile.write(u)
            else:                                                      
                s.serverSteal(path)                                
                self.send_response(200)                              
                fileType = path.split('.')[-1]  
                             
                try:
                    self.send_header('Content-type',contentTypes[fileType]) 
                except KeyError:                                        
                    self.send_header('Content-type',contentTypes['htm']) 
                    serverLogger.error('Unknown MIME content-type for file: [%s]. Reverting to default text/html',path)                     
                self.end_headers()   
                #TODO: Should we open ALL files in binary-read mode?                                  
                if fileType in binaryFiles:                             
                    f = open(sourceDir+path, 'rb')                         
                else: 
                    f = open(sourceDir+path)                                
                self.wfile.write(f.read())                             
                f.close()                                              

        def do_POST(self):            
            ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
            if ctype == 'multipart/form-data':
                postvars = cgi.parse_multipart(self.rfile, pdict)
            elif ctype == 'application/x-www-form-urlencoded':
                length = int(self.headers.getheader('content-length'))
                postvars = cgi.parse_qs(self.rfile.read(length), keep_blank_values=1)
            else:
                return
            s.save._checkProjectData()
            if 'downloadProject' in self.path:   
                #We're TECHNICALY supposed to send this back to the client, but we save locally instead
                data = ast.literal_eval(postvars['data'][0])
                s.save.writeSave(data['name'],
                                 projectDir,
                                 postvars['data'][0])
                self.send_response(200)

            elif 'saveProject' in self.path:
                for idx in range(0,len(postvars['state'])):
                    data = postvars['state'][idx]
                    name = postvars['title'][idx]
                    id = s.save.writeSave(name, projectDir, data)
                self.send_response(200)
                self.send_header('Content-Type','text/html')
                self.end_headers()

                json_obj = json.dumps({"ProjectID": id, "UserID": s.save.user})
                u = unicode(str(json_obj), "utf-8")
                self.wfile.write(u)

            elif 'updateProject' in self.path:
                data = postvars
                id = postvars['ProjectID'][0]

                newData = ast.literal_eval(postvars['state'][0])
                oldData = ast.literal_eval(s.save.readSave(id))                
                oldData.update(newData)
                s.save.writeTruncateSave(id,projectDir,oldData)

                self.send_response(200)
                self.send_header('Content-Type','text/html')
                self.end_headers()

                json_obj = json.dumps({"ProjectID": id, "UserID": s.save.user})
                u = unicode(str(json_obj), "utf-8")
                self.wfile.write(u)

            elif 'loadProject' in self.path:
                data = s.save.readSave(postvars['ProjectID'][0])
                data = ast.literal_eval(data)

                self.send_response(200)
                self.send_header('Content-Type','text/html')
                self.end_headers()

                json_obj = json.dumps({"state": str(data).replace("'",'"')})
                u = unicode(str(json_obj), "utf-8")
                self.wfile.write(u)
                
            elif 'deleteProject' in self.path:
                logging.error('Cannot process request: %s',self.path)

                self.send_response(200)
                s.save.psuedoDelete(postvars['ProjectID'][0],projectDir)

            else:
                logging.error('Cannot process request: %s',self.path)
                    
        def log_error(self, format, *args):
            serverLogger.error(format,*args)
        def log_message(self,format, *args):
            serverLogger.debug(format,*args)

    class SaveHandler:
        """
        Contains functions for writing, reading, and deleting ModKit save files 
        (Basically just JSON text). This class also handles keeping track
        of the current list of ModKit saves and the associated metadata
        """
        def __init__(self):
            self.user = "tnter1234@gmail.com"
            self.projectData = {"projects": []}
            self._checkProjectData()

        def writeSave(self,name,path,data):
            """
            Create a new save file and write data to it. 
            Will create a new file if the requested file already exists
            """
            for id in range(0,501):
                file = '%s/%s-%i.mkc' %(path,name,id)           
                if not os.path.isfile(file):
                    break

            f = open(file,'a')                          
            f.write(data) 
            logging.info('Wrote %s bytes to file: (%s)',
                          len(str(data)),file)                              
            f.close() 

            projData = {"ProjectID": '%s-%i' %(name,id) , 
                        "updated": time.strftime('%a %b %d %H:%M:%S %Y',   #Thu Aug 21 09:21:40 2014
                                                 time.localtime(os.path.getmtime(file))), 
                        "UserID": self.user, 
                        "title": name}

            self.projectData['projects'].append(projData)
            return '%s-%i' %(name,id) 

        def writeTruncateSave(self,name,path,data):
            """
            Create a save file and write data to it. 
            WARNING: Will truncate (overwrite) the file if a file of the same name exists!
            """
            file = '%s/%s.mkc' %(path,name)
            f = open(file,'w')                          
            f.write(str(data)) 
            logging.info('Truncated file and wrote %s bytes to file: (%s)',
                          len(str(data)),file)                              
            f.close() 

            projData = {"ProjectID": name, 
                        "updated": time.strftime('%a %b %d %H:%M:%S %Y',   
                                                 time.localtime(os.path.getmtime(file))), 
                        "UserID": self.user, 
                        "title": data['name']}
            idx=0
            for project in self.projectData['projects']:
                if project['ProjectID'] == name:                   
                    break
                idx += 1

            self.projectData['projects'].pop(idx)
            self.projectData['projects'].append(projData)
            return name
        def psuedoDelete(self,name,path):
            """
            'Deletes' a file by changing the file type to a .deleted file. 
            Preserves the file data until manual deletion
            """
            file = '%s/%s.mkc'%(path,name)
            try:
                os.rename(file,file+'.deleted')
            except BaseException as er:
                serverLogger.exception(er)

            idx=0
            for project in self.projectData['projects']:
                if project['ProjectID'] == name:                   
                    break
                idx += 1
            serverLogger.debug('Deleted file: %s',name)
            self.projectData['projects'].pop(idx)

        def readSave(self,fileName):
            """
            Read the data out of the save file and return it. 
            """
            emptyFile = not os.path.isfile(projectDir+'/'+fileName+'.mkc')

            f = open(projectDir+'/'+fileName+'.mkc','r+')                          
            data = f.read()
            logging.info('Read %s bytes from file: (%s)',
                          len(str(data)),fileName)                              
            f.close() 
            if emptyFile:
                return '{}'
            return data            
        def _checkProjectData(self):
            """
            Generate MetaData for all existing files in the save folder
            """
            self.projectData = {"projects": []} #Erase the current metadata dict

            for name in os.listdir(projectDir):             #Iterate through the save directory
                path = '%s/%s'%(projectDir,name)            #Create a full file path
                if name.endswith('.deleted'): continue      #ignore the file if it has been 'deleted'
                with open(path,'r') as file:                #Open the file in read-only mode  
                    try:                                   
                        data = ast.literal_eval(file.read())#Invoke the python compiler to convert the string into a dict
                        forName = name.replace('.mkc','')   #Remove the file extention
                                                            #If the file does not have a number at the end
                        if not forName[-1].isdigit() or not forName[-2] == '-':
                            forName += '-0'                 #Add the number

                                    #The ID is the name of the file (unique to file)
                        projData = {"ProjectID": forName, 
                                    #The timestamp of the file's last time it was edited (time format: Thu Aug 21 09:21:40 2014)
                                    "updated": time.strftime('%a %b %d %H:%M:%S %Y', 
                                                             time.localtime(os.path.getmtime(path))), 
                                    #the user ID is the e-mail of the user
                                    "UserID": self.user, 
                                    #The title is the display name (not unique, can have duplicates)
                                    "title": data['name']}
                        #Add the meta to the dict 
                        self.projectData['projects'].append(projData)

                    except BaseException as er:
                        #Log any errors (usually file opening or parsing errors)
                        logging.warning('%s %s\n                          | ERROR: %s',
                                      'Corrupted save file, ignoring:',path,er)

if __name__ == '__main__':  
    #Only run this code if this is the file being run (not imported)

    logFile = '%s/%s.log' % (logDir, #Generate a log file path and name, with the name as a date and timestamp
                             str(datetime.datetime.now()).split('.')[0]
                                                         .replace(':','.'))
    #Initalize the logging module 
    logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s [%(levelname)-7s] %(name)-15s | %(message)s',
                    datefmt='%Y-%d %H:%M:%S',
                    filename=logFile,
                    filemode='w')

    console = logging.StreamHandler() #Get a logging stream handler
    console.setLevel(logging.DEBUG)   #and set it to log debug priority or higher

    #Create a formatting object for logging to the console
    formatter = logging.Formatter('[%(levelname)-7s] %(name)-15s | %(message)s')
    console.setFormatter(formatter)

    logging.getLogger('').addHandler(console) #Add the console handler to the main handler
    logging.captureWarnings(True)             #Allow the Warnings module's warnings to be logged
    serverLogger = logging.getLogger('server.handler') #Create a new logger with a different name for the server handler

    #Print a header to the console only (NOT logged)
    print '[<level>] <name>          | <message>\n--------------------------------------------------'

    #Check if the directories exist and create them if they do not
    logging.info('Checking if main folders exist..')
    if not os.path.exists(sourceDir): 
        logging.info('Webpage source directory does not exist! Creating...')
        os.makedirs(sourceDir)

    if not os.path.exists(logDir):
        logging.info('Log file directory does not exist! Creating...')
        os.makedirs(logDir)

    if not os.path.exists(projectDir):
        logging.info('Project save directory does not exist! Creating...')
        os.makedirs(projectDir)
    logging.info('..Done!')

    s = Server(ip,port)    
    s.ServeForever()       

