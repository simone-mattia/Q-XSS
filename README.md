# Q-XSS
Q-Learning approach to XSS exploitation

```
sudo php -S 127.0.0.1:80 
./qxss.py -u "http://localhost/get.php" -p name
./qxss.py -u "http://localhost/attribute.php" -p name
./qxss.py -u "http://localhost/post.php" -m POST -p comment
./qxss.py -u "http://localhost/cookie.php" -m COOKIE -p testCookie
```