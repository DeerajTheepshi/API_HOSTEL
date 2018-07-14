import socket
import mimetypes
import MySQLdb
import hashlib
import re
import json

#Describe the client 
HOST = '0.0.0.0'
PORT = 9000

#check the username and password (for registration purposes)
def checkUserName(Muser,content,checker):
	if((not Muser) or len(Muser)<5 or len(Muser)>10):
		checker = 1
		return checker
def checkPass(Mpass, content, checker):
	if((not Mpass) or not (len(re.findall('[a-zA-Z]+',Mpass))>0 and len(re.findall('[0-9]+',Mpass))>0 and len(re.findall('[._^%$#!~@-]+',Mpass))>0 )):
		checker = 2
		return checker

#Establish TCP connections using Ports
serSock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serSock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
serSock.bind((HOST, PORT))
serSock.listen(0) #accept a maximum of only one request at a time
print('Listening on port %s ....' %PORT)
while True: 
	con, addr = serSock.accept() #accept requests from the client
	req = con.recv(1024).decode() #Recieve from the client
	print("REQUEST IS: ")
	print(req)

	#PARSE the request
	lines = req.split('\r\n')
	reqMethod = lines[0].split()[0]
	reqPath = lines[0].split()[1]
	content = ""

	print(reqPath)

	#GET REQUEST IS PLACED:
	if(reqMethod == "GET"):

		#match/floorNumber
		if("/match/" in reqPath):
			FloorReq = int(reqPath[-1])
			db = MySQLdb.connect("localhost","root","root","API")
			cursor = db.cursor()

			query = "SELECT * FROM REQUEST WHERE FLOOR_ALLOTTED = '%d'" %FloorReq
			print(query)

			cursor.execute(query)
			data = cursor.fetchall()
			#if no user is found
			if data is None:
				content = "User Doesnt exist"
			else:
				items = []
				for row in data:
					items.append({'id':row[0],'user':row[1],'phone':row[2],'roomAlloted':row[3],'roomNeeded':row[4],'floorNeeed':row[5],'hostelName':row[6],'floorAllotted':row[7]})
					content = json.dumps({'items':items})
			db.close()
				
		
	#POST METHOD IS REQUESTED			
	if(reqMethod == "POST"):
		db = MySQLdb.connect("localhost","root","root","API")
		cursor = db.cursor()
		#Login request
		if( reqPath ==  "/welcome"):
			reqPost = lines[-1]
			#parse the key values pairs
			data = reqPost.split('&&')
			UserName = data[0].split('=')[1]
			PassWord = data[1].split('=')[1]

			query = "SELECT * FROM USERS WHERE USERNAME = '%s' ;" %UserName

			cursor.execute(query)
			data = cursor.fetchall()
			
			#if no user is found
			if data is None:
				content = "User Doesnt exist"
			else:
				hashPassword = data[0][2]
				PassWord = hashlib.sha1(PassWord.encode()).hexdigest() #python hashes are hex digests
				print(hashPassword + " " + PassWord)

				#check if passwords match, if yes serve with welcome content
				if(hashPassword == PassWord):
					items = []
					for row in data:
						items.append({'id':row[0],'user':row[1],'phone':row[3]})
					content = json.dumps({'items':items})
						
				else:
					content = "Invalid Password"
			db.close()

		#register
		if(reqPath == "/register"):
			db = MySQLdb.connect("localhost","root","root","API")
			cursor = db.cursor()
			reqPost = lines[-1]
			data = reqPost.split('&&')
			UserName = data[0].split('=')[1]
			PassWord = data[1].split('=')[1]
			Phone = data[2].split('=')[1]
			checker = 0
			checker = checkUserName(UserName,content,checker)
			if(checker==1):
				content += "username cannot be empty, has to be between 5-10 characters"
			checker = checkPass(PassWord,content,checker)
			if(checker == 2):
				content += "password cannot be empty, must contain one alphabet, one numeric and one special character"
			print(UserName, PassWord,checker)

			
			if(checker is None):
				PassWord = hashlib.sha1(PassWord.encode()).hexdigest()
				query = "INSERT INTO USERS (USERNAME, PASSWORD, PHONE) VALUES ('%s', '%s', '%s')"%(UserName,PassWord,Phone)
				try:
					cursor.execute(query)
					db.commit()
					content += "REGISTRATION SUCCESS"
				except:
					db.rollback()			
			db.close()
		
		#request
		if(reqPath == "/request") :
			db = MySQLdb.connect("localhost","root","root","API")
			cursor = db.cursor()
			reqPost = lines[-1]
			data = reqPost.split('&&')
			UserName = data[0].split('=')[1]
			Phone = data[1].split('=')[1]
			roomAll = int(data[2].split('=')[1])
			roomNeed = int(data[3].split('=')[1])
			floorNeed = int(data[4].split('=')[1])
			hostelName = data[5].split('=')[1]
			notes = data[6].split('=')[1]
			floorAll = int(data[7].split('=')[1])
			
			print(UserName,roomAll,roomNeed,floorNeed,hostelName,notes)			
	
			query = "INSERT INTO REQUEST (USERNAME, PHONE, ROOM_ALLOTTED, ROOM_NEEDED, FLOOR_NEEDED, HOSTEL_NAME, NOTES, FLOOR_ALLOTTED) VALUES ('%s', '%s', '%d','%d','%d','%s','%s','%d')"%(UserName,Phone,roomAll,roomNeed,floorNeed,hostelName,notes,floorAll)

			print(query)
			try:
				cursor.execute(query)
				db.commit()
				content += "REQUEST SUCCESS"
			except:
				db.rollback()			
			db.close()
		
		#reqMade
		if(reqPath == "/requestMade"):
			db = MySQLdb.connect("localhost","root","root","API")
			cursor = db.cursor()
			reqPost = lines[-1]
			data = reqPost.split('&&')
			UserName = data[0].split('=')[1]
			query = "SELECT * FROM REQUEST WHERE USERNAME = '%s' ;" %UserName
			cursor.execute(query)
			data = cursor.fetchall()
			
			#if no user is found
			if data is None:
				content = "User Doesnt exist"
			else:
				items = []
				for row in data:
					items.append({'id':row[0],'user':row[1],'phone':row[2],'roomAlloted':row[3],'roomNeeded':row[4],'floorNeeed':row[5],'hostelName':row[6],'floorAllotted':row[7]})
					content = json.dumps({'items':items})
			db.close()

		
		

		
	response = 'HTTP/1.0 200 OK\n'+'Content-type: text/html; charset=UTF-8\n\n'+content 
	#send the response to the client via the connection
	con.sendall(response.encode())
	con.close()
serSock.close()


	
