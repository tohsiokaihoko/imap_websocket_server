# imap websocket server

## start program
コマンドラインから以下のように server.py を実行して下さい。
    $ python server.py

## login
メールサーバに IMAP で login します。以降、logout するまでセッションを保持します。
login に成功した場合、login 中の全てのユーザに response が送られます。
* request parameters
 * method : 文字列 : "login"
 * mailServer : 文字列 : メールサーバ名
 * mailAddress : 文字列 : メールアドレス
 * password : 文字列 : パスワード

* response members
 * method : 文字列 : "login"
 * mailAddress : 文字列 : メールアドレス


## logout
メールサーバから logout します。
logout に成功した場合、login 中の全てのユーザに response が送られます。
* request parameters
 * method : 文字列 : "logout"

* response members
 * method : 文字列 : "logout"
 * mailAddress : 文字列 : メールアドレス


## idle
login するとidle 状態になり、新着メールを受信すると当該ユーザに response が送られます。
* response members
 * method : 文字列 : "unseen"
 * mailAddress : 文字列 : メールアドレス
 * count：数値：未読メール件数
