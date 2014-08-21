PythonCacheServer
=================

Python HTTP webserver with the ability to download cached content. 
Requirements:
 - Python 2.7
 - Web browser (Chrome recommended)
 
To run:

 1) Put all the files into an empty folder

 2) Run main.py with the PYTHON 2.7 (!) interperter
 
 3) Wait for any file downlaods to finish (if any)
 
 4) Go to http://<ip>:<port>  (default is http://localhost:5042)


Default Config:

ip = 'localhost'            <---The internal IP and port that the HTTP server will be started on
port = 5042

liveURL = 'http://www.modkit.com/vex/editor'

sourceDir = 'modkitSource'  <---This is the folder where the page's source will be cached/read from

projectDir = 'Projects'     <---Projects that are sent to the server on a POST request are saved here

logDir = 'logs'             <---Console logs are saved here with a date and timestamp

dumpURLs = logDir+'/listAllURL.txt' <---This file stores a list of files that are known to exist 

downloadFilesOnStartup = True  <---Will attempt to download files that it does not have and are listed in dumpURLs on startup

logLevel = [0,1,2,3,4]      <---If the message's level is in this list, it will be printed to console
