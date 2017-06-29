##   OPS    #######

made AWS EC2 with mongoDB and scraped 656 pages of games tagged as indie

ssh -NfL localhost:9000:localhost:8888 tombstone

http://localhost:9000/?token=d23ef16458d05119554bfa7af2a95efc273cee49494dc21e

open notebook using port 9000!

http://localhost:9000/?token=15a3ecc24a52ce62e21cd4879fbb2ca20ad089662c7298b3


## Generate SSH Key ####
###on AWS EC2 server:
cd ~/.ssh
ssh-keygen
<enter>
<enter>
<enter>
(mash enter a few times)

Should see:
ubuntu@ip-172-31-14-145:~/.ssh$ ssh-keygen
Generating public/private rsa key pair.
Enter file in which to save the key (/home/ubuntu/.ssh/id_rsa):
Enter passphrase (empty for no passphrase):
Enter same passphrase again:
Your identification has been saved in /home/ubuntu/.ssh/id_rsa.
Your public key has been saved in /home/ubuntu/.ssh/id_rsa.pub.

The key fingerprint is:
SHA256:hrNV5BthKwdEc5LbABl1hc/mQn1NOnLu0BCkZ2UigOU ubuntu@ip-172-31-14-145
The key's randomart image is:
+---[RSA 2048]----+
|      oXXoB++ o  |
|      o.oX.=.+  .|
|        E+B+o. + |
|       ..+o=B = .|
|      o S..o B . |
|       =  . o o  |
|      .    . o   |
|              .  |
|                 |
+----[SHA256]-----+

######then do:
more id_rsa.pub

######should see a bunch of random looking letters
ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC40QzD1oxqPf+9
<snip>
wd+j6gKh4/sseCBN ubuntu@ip-172-31-14-145

######copy and paste that into github (or whatever) public key

## tmux stuff #########

### logged in to remote AWS EC2 server
tmux new-session -s work

###do stuff ie jupyter notebook
###exit from terminal to drop back to local terminal

###re-ssh to remote server

tmux attach -t work

###should reattach you to the jupyter notebook

## Anaconda installer  ###########

wget https://repo.continuum.io/archive/Anaconda2-4.4.0-Linux-x86_64.sh
bash Anaconda2-4.4.0-Linux-x86_64.sh


## Install MongoDB     ###########

https://www.howtoforge.com/tutorial/install-mongodb-on-ubuntu-16.04/


## MONGO DB is weird ######

> db.users.save( {username:"mkyong"} )
> db.users.find()
{ "_id" : ObjectId("4dbac7bfea37068bd0987573"), "username" : "mkyong" }
>
> show dbs
admin   0.03125GB
local   (empty)
mkyongdb        0.03125GB

##############################

###### create new database collection
db.createCollection("new_collection")


## Nginx config file
/etc/nginx/sites-enabled/

config file is:  default

the path to the server is under root /var/www/html; if it hasn't been changed

therefore you can modify the files in /var/www/html and the nginx will use that

Proxy to redirect nginx to flask
change default file here:

location / {
                # First attempt to serve request as file, then
                # as directory, then fall back to displaying a 404.
                # try_files $uri $uri/ =404;
                proxy_pass http://localhost:5000;
        }

since we modified the config file we have to restart the nginx process

sudo service nginx reload

# verify if flask is working

######ssh -NfL localhost:9900:localhost:<flask port on web server> <ssh alias to webserver>
######ex:
ssh -NfL localhost:9900:localhost:5000 webserver

###### once that tunnel is established from your laptop to the EC2 in your laptop
###### try opening a browser to
http://localhost:9900
###### and see if that works. If yes then seems like flask is good

######################################
# verify if nginx is working
######################################

###### make a new ssh tunnel to test nginx. the point of this is to bypass AWS
###### security profile rules which is a common failure mode (AWS security blocking ports)

ssh -NfL localhost:9901:localhost:80 webserver

###### once that tunnel is established from your laptop to the EC2 in your laptop
###### try opening a browser to
http://localhost:9901
###### and see if that works. If yes then seems like nginx is good

###### if it doesn't work then nginx is trying to serve on a different port
###### or the process isn't running.  use stuff like ps aux or the lsof -i :8080
###### to try to figure out where it is running
