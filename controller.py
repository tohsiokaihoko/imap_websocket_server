#!/usr/bin/env python
#-*- coding:utf8 -*-
import json
import imaplib2
import time
from idle import Idler 

class AppController:
    def __init__(self, server):
        self.server = server
        self.CLIENT_LOGIN = False

    def login(self, params):
		try:
			mailServer = params["mailServer"]
			mailAddress = params["mailAddress"]
			password = params["password"]
		except KeyError, e:
			self.sendError(501, "Syntax error in parameters or arguments /%s" % e)
			return
		except ValueError, e:
			self.sendError(501, "members Syntax error in parameters or arguments /%s" % e)
			return

		if not self.CLIENT_LOGIN:
			self.CLIENT_LOGIN = True
			self.mailServer = mailServer
			self.mailAddress = mailAddress
			try:
				M = imaplib2.IMAP4_SSL(self.mailServer)
				M.login(self.mailAddress,password)
				M.select("INBOX")
				self.idler = Idler(M)
				self.idler.setDosync(self.dosync)
				self.idler.start()
			except Exception,e:
				print e
				# Clean up.
				self.idler.stop()
				self.idler.join()
				self.idler.M.close()
				self.idler.M.logout()

			self.sendDataForAll({'method':params['method'], 'mailAddress':self.mailAddress})
		else:
			self.sendError(500, 'Already logged in')

    def logout(self, params):
        if self.CLIENT_LOGIN:
            self.CLIENT_LOGIN = False
            try:
                self.idler.stop()
                self.idler.join()
                self.idler.M.close()
                self.idler.M.logout()
            except Exception,e:
                print e
            self.sendDataForAll({'method':params['method'], 'mailAddress':self.mailAddress})
        else:
            self.sendError(500, 'Not logged in')

    def dosync(self):
        print "Call AppController::dosync"
        typ,nums = self.idler.M.search("UTF-8", "unseen")
        UIDs = [int(uid) for uid in nums[0].split()]
        print "Unseen message:%d" % len(nums[0].split())
        print "UIDs:%s" % UIDs
        self.sendData({'method':'unseen', 'mailAddress':self.mailAddress, 'count':len(nums[0].split())})

    def sendData(self, data):
        self.server.sendDataFrame(data)

    def sendDataForAll(self, data):
        self.server.broadcastDataFrame(data)

    def sendError(self, code, message):
        self.server.sendDataFrame({'error':{'code':code, 'message':message},})