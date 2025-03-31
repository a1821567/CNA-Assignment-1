# Include the libraries for socket and system calls
import socket
import sys
import os
import argparse
import re

# STEP 1
# 1. What HTTP request will the browser send to the proxy?
#     GET
# 2. What will the HTTP response look like?
#     HTTP/1.1 200 OK
#     Date: ...
#     Server: ...
#     Content-Type: ...
#     Content-Length: ...
#     <html>...</html>
# 3. In what ways will the response look different if it 
# comes from the proxy than if it comes from the origin server 
# (i.e. the server where the original page is stored?). You 
# will not be able to test this yet, but what do you think 
# would happen?
#     Additional header to indicate that the response has come through a proxy

# STEP 2
# 1. How will the client know to talk to the proxy?
#     Client may set the proxy address and port in their browser or network settings.
#     Can also use curl command.
# 2. What host and port number will the proxy be on?
#     Host: localhost
#     Port: 8080
# 3. The proxy may need to connect to the origin server 
# (if the web object is not in the cache), what host and 
# port number will the proxy connect to?
#     Default port: 80
#     Host: from URI
# 4. Where will the proxy get the web object information?
#    From the origin server (make a GET request)

# STEP 8
# Should 301 and 302 responses be cached?
#     301 indicates a permanent move, so should be cached.
#     302 indicates a temporary move, so should not be cached.

# 1MB buffer size
BUFFER_SIZE = 1000000

# Get the IP address and Port number to use for this web proxy server
parser = argparse.ArgumentParser()
parser.add_argument('hostname', help='the IP Address Of Proxy Server')
parser.add_argument('port', help='the port number of the proxy server')
args = parser.parse_args()
proxyHost = args.hostname
proxyPort = int(args.port)

# Create a server socket, bind it to a port and start listening
try:
  # Create a server socket
  # ~~~~ INSERT CODE ~~~~
  proxySocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  # ~~~~ END CODE INSERT ~~~~
  print ('Created socket')
except:
  print ('Failed to create socket')
  sys.exit()

try:
  # Bind the server socket to a host and port
  # ~~~~ INSERT CODE ~~~~
  proxySocket.bind(('', proxyPort))
  # ~~~~ END CODE INSERT ~~~~
  print ('Port is bound')
except:
  print('Port is already in use')
  sys.exit()

try:
  # Listen on the server socket
  # ~~~~ INSERT CODE ~~~~
  proxySocket.listen(1)
  print("The proxy is ready to receive")
  # ~~~~ END CODE INSERT ~~~~
  print ('Listening to socket')
except:
  print ('Failed to listen')
  sys.exit()

# continuously accept connections
while True:
  print ('Waiting for connection...')
  clientSocket = None

  # Accept connection from client and store in the clientSocket
  try:
    # ~~~~ INSERT CODE ~~~~
    clientSocket, addr = proxySocket.accept() # connection to client, create new socket for communication with client
    # ~~~~ END CODE INSERT ~~~~
    print ('Received a connection')
  except:
    print ('Failed to accept connection')
    sys.exit()

  # Get HTTP request from client
  # and store it in the variable: message_bytes
  # ~~~~ INSERT CODE ~~~~
  message_bytes = clientSocket.recv(1024) # receive up to 1024 bytes from client
  # ~~~~ END CODE INSERT ~~~~
  message = message_bytes.decode('utf-8')
  print ('Received request:')
  print ('< ' + message)

  # Extract the method, URI and version of the HTTP client request 
  requestParts = message.split()
  method = requestParts[0]
  URI = requestParts[1]
  version = requestParts[2]

  print ('Method:\t\t' + method)
  print ('URI:\t\t' + URI)
  print ('Version:\t' + version)
  print ('')

  # Get the requested resource from URI
  # Remove http protocol from the URI
  URI = re.sub('^(/?)http(s?)://', '', URI, count=1)

  # Remove parent directory changes - security
  URI = URI.replace('/..', '')

  # Split hostname from resource name
  resourceParts = URI.split('/', 1)
  hostname = resourceParts[0]
  resource = '/'

  if len(resourceParts) == 2:
    # Resource is absolute URI with hostname and resource
    resource = resource + resourceParts[1]

  print ('Requested Resource:\t' + resource)

  # Check if resource is in cache
  try:
    if statusCode != 302: # no caching for 302
      safeHostname = re.sub(r'[<>:"/\\|?*]', '_', hostname) # sanitise to prevent errors (particularly on Windows for testing)
      safeResource = re.sub(r'[<>:"/\\|?*]', '_', resource)
      cacheLocation = './' + safeHostname + safeResource
      if cacheLocation.endswith('/'):
          cacheLocation = cacheLocation + 'default'

      print ('Cache location:\t\t' + cacheLocation)

      fileExists = os.path.isfile(cacheLocation)
      
      # Check whether the file is currently in the cache
      cacheFile = open(cacheLocation, "r")
      cacheData = cacheFile.readlines()

      print ('Cache hit! Loading from cache file: ' + cacheLocation)
    # ProxyServer finds a cache hit
    # Send back response to client 
    # ~~~~ INSERT CODE ~~~~
    clientSocket.sendall("".join(cacheData).encode())
    # ~~~~ END CODE INSERT ~~~~
    cacheFile.close()
    print ('Sent to the client:')
    print ('> ' + "".join(cacheData))
  except:
    # cache miss.  Get resource from origin server
    originServerSocket = None
    # Create a socket to connect to origin server
    # and store in originServerSocket
    # ~~~~ INSERT CODE ~~~~
    originServerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # ~~~~ END CODE INSERT ~~~~

    print ('Connecting to:\t\t' + hostname + '\n')
    try:
      # Get the IP address for a hostname
      address = socket.gethostbyname(hostname)
      # Connect to the origin server
      # ~~~~ INSERT CODE ~~~~
      originServerSocket.connect((address, 80))
      # ~~~~ END CODE INSERT ~~~~
      print ('Connected to origin Server')

      originServerRequest = ''
      originServerRequestHeader = ''
      # Create origin server request line and headers to send
      # and store in originServerRequestHeader and originServerRequest
      # originServerRequest is the first line in the request and
      # originServerRequestHeader is the second line in the request
      # ~~~~ INSERT CODE ~~~~
      originServerRequest = f"GET {resource} HTTP/1.1"
      originServerRequestHeader = f"Host: {hostname}\r\nConnection: close"
      # ~~~~ END CODE INSERT ~~~~

      # Construct the request to send to the origin server
      request = originServerRequest + '\r\n' + originServerRequestHeader + '\r\n\r\n'

      # Request the web resource from origin server
      print ('Forwarding request to origin server:')
      for line in request.split('\r\n'):
        print ('> ' + line)

      try:
        originServerSocket.sendall(request.encode())
      except socket.error:
        print ('Forward request to origin failed')
        sys.exit()

      print('Request sent to origin server\n')

      # Get the response from the origin server
      # ~~~~ INSERT CODE ~~~~
      response = originServerSocket.recv(4096)

      # Extract status code (for controlling cache handling for 302)
      responseStr = response.decode('utf-8', errors='ignore')
      responseLines = responseStr.split("\r\n")
      statusCode = int(responseLines[0].split()[1])
      # ~~~~ END CODE INSERT ~~~~

      # Send the response to the client
      # ~~~~ INSERT CODE ~~~~
      clientSocket.sendall(response)
      # ~~~~ END CODE INSERT ~~~~

      if statusCode != 302: # temporary redirect - do not cache response
        # Create a new file in the cache for the requested file.
        cacheDir, file = os.path.split(cacheLocation)
        print ('cached directory ' + cacheDir)
        if not os.path.exists(cacheDir):
          os.makedirs(cacheDir)
        cacheFile = open(cacheLocation, 'wb')

        # Save origin server response in the cache file
        # ~~~~ INSERT CODE ~~~~
        cacheFile.write(response)
        # ~~~~ END CODE INSERT ~~~~
        cacheFile.close()
        print ('cache file closed')

      # finished communicating with origin server - shutdown socket writes
      print ('origin response received. Closing sockets')
      originServerSocket.close()
       
      clientSocket.shutdown(socket.SHUT_WR)
      print ('client socket shutdown for writing')
    except OSError as err:
      print ('origin server request failed. ' + err.strerror)

  try:
    clientSocket.close()
  except:
    print ('Failed to close client socket')
