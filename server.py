#!/usr/bin/env python
#-*- coding:utf-8 -*-
from optparse import OptionParser
import SocketServer
import struct
import hashlib
import itertools
import sha
import base64
import json
from WebSocketFrame import WebSocketFrame
from controller import AppController

ws_list = set()

class WebsocketHandler(SocketServer.BaseRequestHandler):
    def handle(self):

        # handler リストに追加
        ws_list.add(self)

        # Handshakeを確立する
        self.handshake(self.request.recv(1024))

        # Controller オブジェクト生成
        self.controller = AppController(self)
        
        # クライアントとの相互通信
        while True:
            data = self.request.recv(1024)
            if not len(data):
                self.closeConnection()
                break
            self.checkDataFrame(data)
            
    def checkDataFrame(self, data):
        '''ハンドシェイク後に受信したデータを解釈する
        '''
        self.frameObj = WebSocketFrame(data)
        if self.frameObj.opcode == 0x8:
            statusCode = self.frameObj.getStatusCode()
            print 'closed Frame(%d) rec' % statusCode
            sendData  = chr(0x88)  # FINビットとクローズフレームを意味するopstatusCodeの値
            sendData += chr(0x02)  # ステータスコードの長さは2バイト
            s = '%04x' % statusCode
            for start in range(0, len(s), 2):
                sendData += chr(int(s[start:start+2], 16))
            self.request.send(sendData)
        else:
            receivedData = self.frameObj.getPayloadData()
            print '[%s:%s] [%s]' % (self.client_address[0], self.client_address[1], receivedData)
            self.callController(receivedData)

    def callController(self, data):
        '''コントローラを呼び出す
        '''
        try:
            req = json.loads(data)
        except Exception, e:
            print e
            self.sendDataFrame({'error':{'code':500, 'message':'Syntax error'},})
            return

        err = {"error":{"code":500, "message":"unknown method"},}
        if "method" in req:
            if hasattr(self.controller, req["method"]):
                method = getattr(self.controller, req["method"])
                if callable(method):
                    try:
                        method(req)
                        return
                    except Exception,e:
                        print('Controller raise Exception / %s',e)
                        err = {"error":{"code":451, "message":"internal error"}}
                        #raise
        self.sendDataFrame(err)

    def broadcastDataFrame(self, data):
        '''接続中の全clientにブロードキャストする
        '''
        data = json.dumps(data)
        sendData  = chr(0x81)  # FINビットとテキストフレームを意味するopcodeの値
        sendData += chr(len(data.encode('utf-8')))
        sendData += data.encode('utf-8')
        print 'len(ws_list):', len(ws_list)
        for s in ws_list:
            try:
                s.request.send(sendData)
            except Exception:
                continue

    def sendDataFrame(self, data):
        '''接続中のclientにデータを送信する
        '''
        data = json.dumps(data)
        sendData  = chr(0x81)  # FINビットとテキストフレームを意味するopcodeの値
        sendData += chr(len(data.encode('utf-8')))
        sendData += data.encode('utf-8')
        self.request.send(sendData)

    def closeConnection(self):
        '''クライアントに対してclosing-frameを送信する
        '''
        print 'closing-frame send to %s:%s' % (self.client_address[0], self.client_address[1])
        ws_list.remove(self)
        self.request.send('\xFF\x00')
        self.finish()

    def handshake(self, data):
        '''クライアントとハンドシェイクを確立する
        '''
        print '<' * 10, 'rec handshake data from %s:%s' % (self.client_address[0], self.client_address[1])
        print data
        print '<' * 40

        (fields, key) = self.parse(data)
        print (fields, key)
        self.sendHandshake(fields, key)

    def parse(self, data):
        '''クライアントから受信したハンドシェイクデータを解析する
        '''
        # 2行目以降の連続したフィールドをバラす
        fields = data.split('\r\n')
        blankLine = False
        d = dict()
        key = ''
        for field in fields[1:]:
            if field == '':
                blankLine = True
                continue
            if not blankLine:
                fieldName, fieldValue = field.split(': ', 1)
                d[fieldName.lower()] = fieldValue  # フィールド名は大文字と小文字を区別しない
            else:
                key = field
                break
        return (d, key)

    def decode(self, s):
        '''ハンドシェイク中のキーを解析する
        '''
        n = filter(lambda c : c.isdigit(), s)
        m = filter(lambda c : c == ' '   , s)
        return int(n) / len(m)

    def sendHandshake(self, fields, key):
        '''クライアントにハンドシェイクを送信する
        '''
        # Sec-WebSocket-Locationフィールドの値を作成
        LOCATION = 'wss://' if SECURE_FLAG else 'ws://'
        LOCATION += HOST
        LOCATION += ':' + str(PORT) if PORT else ''
        LOCATION += RESOURCE_NAME

        # チャレンジレスポンス
        #part1 = self.decode(fields['sec-websocket-key1'])
        #part2 = self.decode(fields['sec-websocket-key2'])
        #CHALLENGE = struct.pack('>I', part1)  # 値を32bitのビッグエンディアンのバイナリーにする
        #CHALLENGE += struct.pack('>I', part2) # 値を32bitのビッグエンディアンのバイナリーにする
        #CHALLENGE += key
        #RESPONSE = hashlib.md5(CHALLENGE).digest() # /chalenge/のMD5 fingerprintを/response/に入れる
        s = fields['sec-websocket-key'] + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"      #add
        digest = hashlib.sha1(s).digest()                                   #add
        RESPONSE = base64.encodestring(digest)                              #add
        
        # 送信するハンドシェイクデータの作成
        handshakeData = 'HTTP/1.1 101 WebSocket Protocol Handshake\r\n'
        handshakeData += 'Upgrade: WebSocket\r\n'
        handshakeData += 'Connection: Upgrade\r\n'
        handshakeData += 'Sec-WebSocket-Accept: ' + RESPONSE + '\r\n'       #add
        #handshakeData += 'Sec-WebSocket-Origin: ' + ORIGIN + '\r\n'
        #handshakeData += 'Sec-WebSocket-Location: ' + LOCATION + '\r\n'
        #if PROTOCOL:
        #    handshakeData += 'Sec-WebSocket-Protocol: ' + PROTOCOL + '\r\n'
        #handshakeData += '\r\n' + RESPONSE
        self.request.send(handshakeData)  # ハンドシェイクデータの送信

if __name__ == "__main__":
    usage = u'%prog [-p ポート番号] オリジン [-s サブプロトコル名] [-r リソース]'
    parser = OptionParser(usage=usage)
    parser.add_option('-p', '--port', dest='port', type='int', default=8080,help=u'ポート番号(デフォルトは8080)')
    parser.add_option('-s', '--subprotocol', dest='subprotocol', help=u'サブプロトコル名')
    parser.add_option('-r', '--resource', dest='resource', default='/', help=u'リソース')
    options, args = parser.parse_args()
    #if len(args) < 1:
    #    parser.error('引数を1つ入力してください')
    #elif len(args) > 1:
    #    parser.error('引数が多いです')

    HOST = 'localhost'
    PORT = options.port
    #ORIGIN = args[0]
    ORIGIN = ''
    PROTOCOL = options.subprotocol
    RESOURCE_NAME = options.resource
    SECURE_FLAG = False

    SocketServer.ThreadingTCPServer.allow_reuse_address = True
    server = SocketServer.ThreadingTCPServer((HOST, PORT), WebsocketHandler)

    print 'Ctrl-c to exit'
    server.serve_forever()
