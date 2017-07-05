robomongo, use indexes in mongodb to speed things up

#### still looking for a good url to scrape review info from
`http://store.steampowered.com/app/413150/Stardew_Valley/`

not really useful, game achievement stuff:
'http://api.steampowered.com/ISteamUserStats/GetSchemaForGame/v2/?key=5DA6749271B3262B589F2980379B9AE2&appid=413150'

not really useful, game info for a specific user and game
`http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key=XXXXXXXXXXXXXXXXXXXXXXX&steamids=76561197960435530`

`http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key=5DA6749271B3262B589F2980379B9AE2&steamids=76561197960435530`

# Super special shiny unicorn rainbow URL
`http://steamcommunity.com/app/582550/homecontent/?userreviewsoffset=40&p=5&workshopitemspage=5&readytouseitemspage=5&mtxitemspage=5&itemspage=5&screenshotspage=5&videospage=5&artpage=5&allguidepage=5&webguidepage=5&integratedguidepage=5&discussionspage=5&numperpage=10&browsefilter=toprated&browsefilter=toprated&appid=582550&appHubSubSection=10&appHubSubSection=10&l=english&filterLanguage=default&searchText=`

`http://steamcommunity.com/app/582550/homecontent/?userreviewsoffset=40&p=5`

Review page url:
`view-source:http://steamcommunity.com/app/582550/reviews/?p=1`

`http://steamspy.com/api.php`

probably use the 'userreviewoffset=40' as well as the 'p=5' to load in all of the pages

Urls for possible steam scraping:

`http://steamcommunity.com/app/413150/reviews/`
`http://steamcommunity.com/app/413150/reviews/?p=1&browsefilter=toprated`
`http://steamcommunity.com/app/366090/reviews/?browsefilter=snr=1_5_reviews_`

`https://steamcommunity.com/id/simplychen/games/?tab=all`

Output Formats
All API calls take the form http://api.steampowered.com/<interface name>/<method name>/v<version>/?key=<api key>&format=<format>.
Format can be any of:
json - The output will be returned in the JSON format
xml - Output is returned as an XML document
vdf - Output is returned as a VDF file.
If you do not specify a format, your results will be returns in the JSON format.

#######################
#####    IDEA   #######
#######################
normalize how many hours someone has played against the hours on the current game

possible scraping flow for initial run:
  * look at games with indie game tag
  * go through pages of indie games, gathering game id tags
  * use the app id to generate the super special shiny unicorn rainbow URL in order to harvest
      the reviews.
    * Can also try to harvest some user_id's from the reviews but they're probably not
      representative.

#######################
#####    RISKS  #######
#######################

* It seems like very few players actually review games
* Could possibly use 'hours played' to figure out actual 'how much they like something'
  * Problem is some games are open ended and others are close ended, might be
    able to compensate for this by using genre (ie FPS or online or multi-player)
* If I make a list of players from reviewers then this isn't necessarily a representative
  population of players.





  Attempt: 4089 profiles attempted/found so far: 926 / 4090
  <Response [200]> user_id: 76561197983845855
  ---------------------------------------------------------------------------
  IndexError                                Traceback (most recent call last)
  <ipython-input-186-d93118dbbc69> in <module>()
       60             # find the username in the profile info stuff
       61             para = soup.find_all("p")
  ---> 62             user_id = str(para)[str(para).find("personaname"):].split(",")[0].split(" ")[1].strip('"')
       63             attempt_to_get_user_profile(user_id, good_path.format(user_id), profile_error)
       64             print

  IndexError: list index out of range
