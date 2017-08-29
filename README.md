# CallbackBot
A customizeable callback bot for discord. Includes a markov chain generator and emoji polling
## Dependencies
- [python3](https://www.python.org/downloads/)
- [discord.py](https://github.com/Rapptz/discord.py)
  - `python3 -m pip install -U discord.py`
- [markovify](https://github.com/jsvine/markovify)
  - `pip install markovify`
## Adding and running the bot

### Adding the bot to your channel

1. Go to https://discordapp.com/developers/applications/me, login, and add a new app
    1. Name it whatever you want your bot's username to be
    2. Add a profile picture if you want!
2. On the application page click "Create a Bot User"
    1. Check public if you don't care about other people using your bot, otherwise ignore these new options
3. Under Username it should say "Token:click to reveal". Reveal the token and save it for the config
4. Under App Details it should say "Client ID: \[numbers\]"
    1. **Note: this is the ID, not the secret**
    2. Copy the ID into this URL replacing CLIENTID https://discordapp.com/oauth2/authorize?client_id=CLIENTID&scope=bot&permissions=0
    3. It will ask you which servers to add it to, you can only add it to servers that you have management permissions on
    
#### Your bot should be added to the channel! But it's offline, so we need to do a few things to actually get it up and running.
1. Edit the config
    1. In the repo you should see "config.example.json" copy this file and edit the filename to be "config.json"
    2. Edit the file, and replace "token goes here" with the token revealed in step 3 of the last part
2. Run the bot
    1. [Make sure you've downloaded the dependencies](#Dependencies)
    2. Start up a command prompt or bash window and cd to the directory that has callbackBot.py (or whatever you've renamed it to)
    3. run `python3 callbackBot.py`
3. That's it! Your bot should be ready to accept commands now.

### Running the bot
`python3 callbackBot.py`
## Writing Callbacks
Callbacks are written using branching logic trees in the form of JSON objects.
