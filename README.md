# narcov
A customizeable callback bot for discord. Includes a markov chain generator and emoji polling
***Note: to speed up generating markov chains, the bot saves your chat history locally. I am not responsible for any data leaked for this reason, you have been warned.***

**Less scary note: because it'll pull lots and lots of chat history at once, it takes a while to warm up the first time you turn it on. Be patient! It uses saved data after the first pull, so it'll be much faster if you ever need to restart it.**
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

## Build in functions
There are a few build in functions that behave differently from callbacks since they can take arguments or are otherwise run as their own commands, not necessarily part of everyday speech. Functions start with a ! (e.x. "!markov") and the bot will try to tokenize anything you send after the first command into a list of arguments.

Available functions are:

### !markov
Generates a (usually funny) sentence using a markov chain built from your (or your friends') chat history. Usage: `!markov threedliams`

!markov can also be run on yourself without having to type your username by using `!markov me`, or on everyone's chat history at once using `!markov everyone`

### !magic
Gives a random magic 8 ball response to your yes or no question. Usage: `!magic will it rain today?`

### !poll
Creates a poll based on the topic and options you give it that can be voted on by reacting with different emojis. Currently only supports 11 options (for the digits 0-10). Usage:

`!poll "Fries or tots?" "fries" "tots"`

Just react to add your vote, or un-react to remove it again!

## Writing Callbacks
Callbacks are written using branching logic trees in the form of JSON objects. Each callback has a key, which is a word or collection of words to look for, and a result, which is an action or set of actions to perform. For an example, check out the example file at `./callbacks/callbacks.json`, or, for more in depth examples, my personal fork of the CallbackBot, [narcov](https://github.com/threedliams/narcov).

The shell of a callback looks like this:
```javascript
{
  "key": {
    // keys go here
  },
  "result": [
    // results go here
  ]
}
```

### Callback Keys
The most basic key is a string that maps to either true if you want to do something when it appears, or false when you want to do something when it doesn't.
```javascript
// this key does something when the word "hello" shows up
"key": {
  "hello": true
}
```
```javascript
// this key does something when the word "hello" *does not* show up
"key": {
  "hello": false
}
```
Doing something every time a word *doesn't* show up would be really annoying by itself, but in combination with some of the next pieces you can create some very specific callbacks.
#### +and
"+and" tells the callback bot that the evaluated truth value of all the keys in the next set are going to be anded together. Or in simpler terms, it looks for two or more keys at once. For example:
```javascript
// this key is equivalent to "...did...you...hear..." where ... can be any other string
// so, for instance, it would match to "did you hear me?", and also "did you hear Susan?"
"key": {
  "+and": [
    {
      "did": true
    },
    {
      "you": true
    },
    {
      "hear": true
    }
  ]
}
```
Or if we want to do something more specific, we can throw in a negation:
```javascript
// this key is equivalent to "...did...you...hear..." where ... can be any other string *that doesn't contain "saw"*
// so, for instance, it would match to "did you hear about this thing?" but *not* "did you hear about the thing I saw?"
"key": {
  "+and": [
    {
      "did": true
    },
    {
      "you": true
    },
    {
      "hear": true
    },
    {
      "saw": false
    }
  ]
}
```

#### +or
"+or" is just like and except it ors instead! For example:
```javascript
// this key is equivalent to "...you/ya/yar/yer..." where ... can be any other string
// so, for instance, it would match to "how are you?" but it would also match "how are ya?"
"key": {
  "+or": [
    {
      "you": true
    },
    {
      "ya": true
    },
    {
      "yar": true
    },
    {
      "yer": true
    }
  ]
}
```

#### Bringing the keys together
Of course this wouldn't be any fun if you couldn't and your ors and or your ands and all that, so here's a more complicated example that brings some of the pieces together:
```javascript
// this key is equivalent to "...did...you/ya...hear...they're/there/their...taking...off...market" where ... can be any other string
// so, for instance, it would match to "did ya hear they're taking benadryl off of the market?"
"key": {
  "+and": [
      {
          "did": true
      },
      {
          "+or": [
              {
                 "you": true
              },
              {
                  "ya": true
              }
          ]
      },
      {
          "hear": true
      },
      {
          "+or": [
              {
                  "they're": true
              },
              {
                  "there": true
              },
              {
                  "their": true
              }
          ]
      },
      {
          "taking": true
      },
      {
          "off": true
      },
      {
          "market": true
      }
  ]
}
```

### Results
Results are whatever actions you want the bot to perform if you match the key you're looking for. The most basic result looks like this:
```javascript
// this result causes the bot to send the message "Hello world!"
"result": [
  {
    "send_message": "Hello world!"
  }
]
```
**Notice** that while "key": {} always maps to an object, "result": [] always maps to an array


Here are all the possible result types you can currently work with:

#### send_message
Sends the message in the value to this key, as in the example above

#### send_file
Uploads a file (such as a picture) to the channel
```javascript
// this result sends "supmello.png" to your channel
"result": [
  {
    "send_file": "./callbacks/supmello.png"
  }
]
```

#### add_reaction
Adds a reaction to whichever message triggered the key. Because of the way that JSON handles unicode, these reactions unfortunately need to be mapped out in the bot itself using the emojiDict variable
```javascript
// this result reacts with the emoji mapped to "call_me" on your message
"result": [
  {
    "add_reaction": "call_me"
  }
]
```

#### run_func
Runs a function when a key is matched. This function can't take arguments like a !function can, it just runs.
```javascript
// this result runs a function called "bird_up"
"result": [
  {
    "run_func": "bird_up"
  }
]
```

#### do_random
This is where it gets interesting, do_random performs a random action or set of actions in its own list of results.
```javascript
// this randomly sends either "Hello!" or "Goodbye!" when your key is matched
"result": [
  {
    "do_random": [
      {
        "send_message": "Hello!"
      },
      {
        "send_message": "Goodbye!"
      }
    ]
  }
]
```

#### Bringing the results all together
As well as doing something random out of a set of results, you can also chain results together to do multiple at once. Here's an example:
```javascript
// this randomly sends either "You're Mellow Mike!" or "You're Bangkok Dangerous!" with the accompanying picture when the key is matched
"result": [
  {
    "do_random": [
      [
        {
          "send_message": "You're Mellow Mike!"
        },
        {
          "send_file": "./callbacks/supmellowmike.png"
        }
      ],
      [
        {
          "send_message": "You're Bangkok Dangerous!"
        },
        {
          "send_file": "./callbacks/bangkokdangerous.png"
        }
      ]
    ]
  }
]
```

### Bringing all the keys and results together
Here's an example of a more complex key and result pair:
```javascript
// this key/result pair matches on "did...you/ya...hear...they're/there/their...taking...off...market" where ... is any other string
// it then sends the message "Why would they take that off the market!?" along with the photo "./callbacks/whywouldthey.png"
{
    "key": {
        "+and": [
            {
                "did": true
            },
            {
                "+or": [
                    {
                       "you": true
                    },
                    {
                        "ya": true
                    }
                ]
            },
            {
                "hear": true
            },
            {
                "+or": [
                    {
                        "they're": true
                    },
                    {
                        "there": true
                    },
                    {
                        "their": true
                    }
                ]
            },
            {
                "taking": true
            },
            {
                "off": true
            },
            {
                "market": true
            }
        ]
    },
    "result": [
        {
            "send_message": "Why would they take that off the market!?"
        },
        {
            "send_file": "./callbacks/whywouldthey.png"
        }
    ]
}
```
