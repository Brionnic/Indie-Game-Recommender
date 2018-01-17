# OPERATIONS CHEAT SHEAT 

###### Brian's most frequently used snippets
`ssh -NfL localhost:9000:localhost:8888 tombstone`

###### Intelligently copy files from a remote server, not copying redundant data:
rsync -av /local/dir/ server:/remote/dir/

###### open notebook using port 9000!

`http://localhost:9000/?token=15a3ecc24a52ce62e21cd4879fbb2ca20ad089662c7298b3`

# Get an EC2 ready to use as a data science/web server after it's been created and spun up

## Generate SSH Key ####
###### on AWS EC2 server:
```
cd ~/.ssh
ssh-keygen
<enter>
<enter>
<enter>
```
###### (mash enter a few times)

###### Should see:
```
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
```

###### then do:
more id_rsa.pub

###### should see a bunch of random looking letters
`ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC40QzD1oxqPf+9
<snip>
wd+j6gKh4/sseCBN ubuntu@ip-172-31-14-145`

###### copy and paste that into github (or whatever) public key

## Anaconda installer  ###########

`wget https://repo.continuum.io/archive/Anaconda2-4.4.0-Linux-x86_64.sh
bash Anaconda2-4.4.0-Linux-x86_64.sh`


## Install MongoDB     ###########

[Installation instructions](https://www.howtoforge.com/tutorial/install-mongodb-on-ubuntu-16.04/)


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

## Python snippet for adding an item to an existing collection while attempting to avoid duplicates
```python
def insert_to_collection(collection, dictionary, match_key):
    '''
    Abstracted insert method which, attempts to add the dictionary to the
    provided collection in MongoDB.  

    The method attempts to avoid duplicate inserts by checking the collection
    to see if there's already an item who's key matches the one being inserted.
    If there is a matching item then the new one is not inserted.
    '''
    if not collection.find_one({match_key: dictionary[match_key]}):
        try:
            collection.insert_one(dictionary)
            print "inserted", dictionary[match_key]

        except Exception, e:
            print "Execption when attempting to insert into collection:", e

    else:
        print match_key, "already exists"
```

## How to read in a MongoDB collection into a pandas DF (Credit Tim :-)  )
```python
import pandas as pd
df = pd.DataFrame(list(your_collection.find()))
```

[More info](https://stackoverflow.com/questions/17805304/how-can-i-load-data-from-mongodb-collection-into-pandas-dataframe/17805626#17805626)

## MongoDB CLI stuff
Enter mongo cli:
`mongo`

show databases:
`> show dbs
capstone  0.233GB
local     0.000GB`

check out database:
`> use capstone
switched to db capstone`

show collections in database:
`> show collections
basic_game_review_scrape
game_app_name_id
game_list_scrape
raw_game_scrape
raw_scraping_data
raw_user_scrape
user_data_digest`

create a collection in database:
`> db.createCollection("test_col")
{ "ok" : 1 }`

verify new addition to database:
`> show collections
basic_game_review_scrape
game_app_name_id
game_list_scrape
raw_game_scrape
raw_scraping_data
raw_user_scrape
test_col            <----------
user_data_digest`

drop collection from database (you know what you're doing, right?):

no really, you're really sure that you want to delete this stuff?
`> db.test_col.drop()
true
> show collections
basic_game_review_scrape
game_app_name_id
game_list_scrape
raw_game_scrape
raw_scraping_data
raw_user_scrape
user_data_digest
`

verify that collection has data (after you've entered stuff into it):
`> db.game_app_name_id.findOne()
{
        "_id" : ObjectId("59519b2b421bd105fddcc3a3"),
        "path" : "http://steamcommunity.com/app/367520/reviews/?p=",
        "app_id" : "367520",
        "title" : "Hollow_Knight"
}`

## Nginx config file
`/etc/nginx/sites-enabled/`

config file is:  `default`

therefore full path to nginx config file would be like:   `nano /etc/nginx/sites-enabled/default`

the path to the server is under root `/var/www/html` if it hasn't been changed

therefore you can modify the files in /var/www/html and the nginx will use that

Proxy to redirect nginx to flask
change default file here:
```
location / {
                # First attempt to serve request as file, then
                # as directory, then fall back to displaying a 404.
                # try_files $uri $uri/ =404;
                proxy_pass http://localhost:5000;
        }
```

#### Important! If you don't restart the service the changes won't take effect
since we modified the config file we have to restart the nginx process

`sudo service nginx reload`

# verify if flask is working

`ssh -NfL localhost:9900:localhost:<flask port on web server> <ssh alias to webserver>`
###### ex:
`ssh -NfL localhost:9900:localhost:5000 webserver`

###### once that tunnel is established from your laptop to the EC2 in your laptop
###### try opening a browser to
`http://localhost:9900`
###### and see if that works. If yes then seems like flask is good

######################################
# verify if nginx is working
######################################

###### make a new ssh tunnel to test nginx. the point of this is to bypass AWS
###### security profile rules which is a common failure mode (AWS security blocking ports)

`ssh -NfL localhost:9901:localhost:80 webserver`

###### once that tunnel is established from your laptop to the EC2 in your laptop
###### try opening a browser to
`http://localhost:9901`
###### and see if that works. If yes then seems like nginx is good

###### if it doesn't work then nginx is trying to serve on a different port
###### or the process isn't running.  use stuff like ps aux or the lsof -i :8080
###### to try to figure out where it is running


## tmux stuff #########

#### Note: => means "then" control+b => %  in English means: press control and 'b' at the same time, then press '%'

###### Connect to tmux session
###### while logged in to remote AWS EC2 server
###### if tmux isn't running, start new session
`tmux`

###### if tmux is running attach to session
`tmux attach`


###### do stuff ie <jupyter notebook>
###### exit from terminal to drop back to local terminal

###### re-ssh to remote server

`tmux attach`

###### should reattach you to the jupyter notebook

###### Extra tmux tips:
###### Create window pane in tmux:

###### Horizontal slice
`ctrl/command + b => "`

###### Vertical slice
`ctrl/command + b => %`

###### Close current pane
`ctrl/command + b => x => y`



## Selenium Stuff

#### Info on running headless (for use on EC2)
[Install Chrome headless and Selenium for Python](https://christopher.su/2015/selenium-chromedriver-ubuntu/)


