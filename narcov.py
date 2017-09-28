
import discord
import os
#TODO: handle unicode better instead of just ignoring it
from unidecode import unidecode
import markovify
import json
from pprint import pprint

import random

client = discord.Client()

savedChannelMap = {}
liveChannelMap = {}
callbackData = {}
polls = []

isSavedReady = False
isLiveReady = False

# Used to get around json's unicode issues
emojiDict = {
    "call_me": "\U0001F919",
    "0": "\U0000FE0F\U00000030\U000020E3",
    "1": "\U0000FE0F\U00000031\U000020E3",
    "2": "\U0000FE0F\U00000032\U000020E3",
    "3": "\U0000FE0F\U00000033\U000020E3",
    "4": "\U0000FE0F\U00000034\U000020E3",
    "5": "\U0000FE0F\U00000035\U000020E3",
    "6": "\U0000FE0F\U00000036\U000020E3",
    "7": "\U0000FE0F\U00000037\U000020E3",
    "8": "\U0000FE0F\U00000038\U000020E3",
    "9": "\U0000FE0F\U00000039\U000020E3",
    "10": "\U0001F51F",
}

################################################################################
# on_ready
#
# When the bot starts up, this runs all the startup functions
#
# Args:
#
#   None
#
# Returns - nothing
################################################################################
@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

    global isSavedReady
    global isLiveReady
    global callbackData

    rootFolder = "./servers/"
    callbackFile = "./callbacks/callbacks.json"

    #load callbackFile
    with open(callbackFile) as data_file:
        callbackData = json.load(data_file)

    #preload any saved channels
    for server in client.servers:
        underscoredServerName = server.name.replace(" ", "_")
        if(os.path.isdir(rootFolder + underscoredServerName)):
            for channel in server.channels:
                underscoredChannelName = channel.name.replace(" ", "_")
                #TODO: channels with the same name on one server?
                if(os.path.isdir(rootFolder + underscoredServerName + "/" + underscoredChannelName)):
                    if not(channel.id in list(savedChannelMap.keys())):
                        savedChannelMap[channel.id] = {}
                    for fileName in os.listdir(rootFolder + underscoredServerName + "/" + underscoredChannelName):
                        f = open(rootFolder + underscoredServerName + "/" + underscoredChannelName + "/" + fileName, 'r')
                        #TODO: handle people with . in their name
                        savedChannelMap[channel.id][fileName.split('.')[0]] = f.read()
    isSavedReady = True

    print("saved ready!")

    #catch up to current logs
    for server in client.servers:
        for channel in server.channels:
            if not(channel.id in list(liveChannelMap.keys())):
                liveChannelMap[channel.id] = {};
            async for log_message in client.logs_from(channel, limit=9999999):
                if not(log_message.author.name in list(liveChannelMap[channel.id].keys())):
                    #TODO: handle username conflicts (discriminator or id)
                    liveChannelMap[channel.id][log_message.author.name] = unidecode(log_message.content)
                else:
                    liveChannelMap[channel.id][log_message.author.name] = liveChannelMap[channel.id][log_message.author.name] + "\n" + unidecode(log_message.content)

    #save current logs for next time
    for server in client.servers:
        underscoredServerName = server.name.replace(" ", "_")
        if not(os.path.isdir(rootFolder + underscoredServerName)):
            os.makedirs(rootFolder + underscoredServerName)
        if(os.path.isdir(rootFolder + underscoredServerName)):
            for channel in server.channels:
                underscoredChannelName = channel.name.replace(" ", "_")
                if not(os.path.isdir(rootFolder + underscoredServerName + "/" + underscoredChannelName)):
                    os.makedirs(rootFolder + underscoredServerName + "/" + underscoredChannelName)
                if(os.path.isdir(rootFolder + underscoredServerName + "/" + underscoredChannelName)):
                    for username in liveChannelMap[channel.id].keys():
                        f = open(rootFolder + underscoredServerName + "/" + underscoredChannelName + "/" + username + ".txt", 'w')
                        f.write(liveChannelMap[channel.id][username])


    isLiveReady = True

    print("live ready!")

################################################################################
# on_message
#
# When someone sends a message in a channel with a bot, this function fires
# so you can process the given message
#
# Args:
#
#   message - the message sent
#
# Returns - nothing
################################################################################
@client.event
async def on_message(message):
    global savedChannelMap
    global liveChannelMap

    global isSavedReady
    global isLiveReady

    tokenizedMessage = tokenize(message.content)

    await functionSwitcher(tokenizedMessage, message)

    if(isSavedReady and not isLiveReady):
        saveMessage(message, savedChannelMap)

    if(isLiveReady):
        saveMessage(message, liveChannelMap)

################################################################################
# on_reaction_add
#
# When someone adds a reaction in a channel with a bot, this function fires
# so you can process the given reaction
#
# Args:
#
#   reaction - the reaction object
#
#   user - the reacting user
#
# Returns - nothing
################################################################################
@client.event
async def on_reaction_add(reaction, user):
    global polls

    isPoll = False
    savedPoll = None
    for poll in polls:
        if(reaction.message.content == poll.content):
            savedPoll = poll
            isPoll = True
    if not(isPoll):
        return

    message = reaction.message
    newPoll = await client.edit_message(message, addVote(message, reaction, user))
    polls.append(newPoll)

################################################################################
# on_reaction_remove
#
# When someone removes a reaction in a channel with a bot, this function fires
# so you can process the given reaction
#
# Args:
#
#   reaction - the reaction object
#
#   user - the reacting user
#
# Returns - nothing
################################################################################
@client.event
async def on_reaction_remove(reaction, user):
    global polls

    isPoll = False
    for poll in polls:
        if(reaction.message.content == poll.content):
            isPoll = True
    if not(isPoll):
        return

    message = reaction.message
    newPoll = await client.edit_message(message, removeVote(message, reaction, user))
    polls.append(newPoll)

################################################################################
# on_reaction_clear
#
# When someone clears a reaction in a channel with a bot, this function fires
# so you can process the given reaction
#
# Args:
#
#   reaction - the reaction object
#
#   user - the reacting user
#
# Returns - nothing
################################################################################
@client.event
async def on_reaction_clear(reaction, user):
    global polls
    isPoll = False

    for poll in polls:
        if(reaction.message.content == poll.content):
            isPoll = True
    if not(isPoll):
        return

    message = reaction.message
    await client.edit_message(message, removeVote(message, reaction, user))

################################################################################
# addVote
#
# Adds a vote to a poll, appending the user's name to the list of votes
#
# Args:
#
#   message - the poll being voted on
#
#   reaction - the vote to consider
#
#   user - the voting user
#
# Returns - nothing
################################################################################
def addVote(message, reaction, user):
    pollText = message.content
    pollLines = pollText.split("\n")

    for i in range(1, len(pollLines), 2):
        splitLine = pollLines[i].split()

        if(unidecode(reaction.emoji) in emojiDict.keys()):
            if(emojiDict[unidecode(reaction.emoji)] == splitLine[0] and i + 1 < len(pollLines)):
                if(pollLines[i+1] == "Votes: none"):
                    pollLines [i+1] = "Votes: \"" + user.name + "\""
                else:
                    pollLines[i+1] += ", \"" + user.name + "\""
                break

    pollText = "\n".join(pollLines)
    return pollText

################################################################################
# removeVote
#
# Removes a vote from a poll, removing the user's name from the list of votes
#
# Args:
#
#   message - the poll being voted on
#
#   reaction - the vote to remove
#
#   user - the voting user
#
# Returns - nothing
################################################################################
def removeVote(message, reaction, user):
    pollText = message.content
    pollLines = pollText.split("\n")

    for i in range(1, len(pollLines), 2):
        splitLine = pollLines[i].split()

        if(unidecode(reaction.emoji) in emojiDict.keys()):
            if(emojiDict[unidecode(reaction.emoji)] == splitLine[0] and i + 1 < len(pollLines)):
                userList = tokenize(pollLines[i+1])
                if(len(userList) == 2):
                    pollLines[i+1] = "Votes: none"
                else:
                    if(userList[1] == "\"" + user.name + "\","):
                        pollLines[i+1].replace("\"" + user.name + "\", ", "")
                    else:
                        pollLines[i+1].replace(", \"" + user.name + "\"", "")

    pollText = "\n".join(pollLines)
    return pollText


################################################################################
# saveMessage
#
# Saves a message into one of the channel maps for later markoving
#
# Args:
#
#   message - the given message
#
#   channelMap - the channel map to save to
#
# Returns - nothing
################################################################################
def saveMessage(message, channelMap):
    if not(message.channel.id in list(channelMap.keys())):
            channelMap[message.channel.id] = {}

    usermap = channelMap[message.channel.id]

    if not(message.author.name in list(usermap.keys())):
        usermap[message.author.name] = unidecode(message.content)
    else:
        usermap[message.author.name] = usermap[message.author.name] + "\n" + unidecode(message.content)

################################################################################
# markov
#
# Generates a markov string for the given user. Supports "me" to markov yourself
# and "everyone" to markov everyone in the channel
#
# Args:
#
#   tokenizedMessage - a tokenized string version of the given message
#
#   message - the original message, used for metadata like the author and channel
#
# Returns - a markov setence in the form of a quote for the given user
################################################################################
def markov(tokenizedMessage, message):
    global isSavedReady
    global isLiveReady

    #TODO: handle username vs other arguments better
    username = ' '.join(tokenizedMessage[1:])

    usermap = None

    channel = message.channel
    author = message.author


    if(isLiveReady):
        usermap = liveChannelMap[channel.id]
    elif(isSavedReady):
        usermap = savedChannelMap[channel.id]
    else:
        return "Sorry, still warming up! Give me a minute. You should only see this message the first time I join a channel."


    compiledLogs = ""

    if not(username in list(usermap.keys())) and not (username == "everyone" or username == "me"):
        return "Sorry I couldn't find a user named '" + username + "'. Usage: !markov [username]"
    elif username == "everyone":
        for each_username in list(usermap.keys()):
            if each_username == client.user.name:
                continue
            compiledLogs = compiledLogs + "\n" + usermap[each_username]
    elif username == "me":
        compiledLogs = usermap[author.name]
    else:
        compiledLogs = usermap[username]

    markov_model = markovify.NewlineText(compiledLogs)

    newSentence = markov_model.make_sentence();
    #if we couldn't generate a sentence, try a few more times to get a valid one
    if(newSentence is None):
        for i in range(5):
            newSentence = markov_model.make_sentence();
            if not(newSentence is None):
                break;

    if(newSentence is None):
        return "Whoops, I tried a few times but it looks like " + username + " needs to talk more before I can generate a good sentence. Try someone else!"
    else:
        if(username == "me"):
            return "\"" + newSentence + "\"\n-" + author.name
        else:
            return "\"" + newSentence + "\"\n-" + username

################################################################################
# magic
#
# Generates a random magic 8 ball response
#
# Args:
#   None
#
# Return - a string of a randomized response
################################################################################
def magic(tokenizedMessage, message):
    random.seed()
    magicOptions = ["It is certain", "It is decidedly so", "Without a doubt", "Yes, definitely", "You may rely on it", "As I see it, yes", "Most likely", "Outlook good", "Yes", "Signs point to yes", "Reply hazy try again", "Ask again later", "Better not tell you now", "Cannot predict now", "Concentrate and ask again", "Don't count on it", "My reply is no", "My sources say no", "Outlook not so good", "Very doubtful"]
    magicResult = magicOptions[random.randrange(len(magicOptions))]
    return magicResult

def createPoll(tokenizedMessage, message):
    #!poll "this is a poll" "yes" "no"
    messageText = tokenizedMessage[1]

    for i in range(2, len(tokenizedMessage)):
        if(i-2 > 10):
            break
        messageText += "\n" + emojiDict[str(i-2)] + " " + tokenizedMessage[i]
        messageText += "\nVotes: none"

    return messageText

#!roll 1d4 10d20
def roll(tokenizedMessage, message):
    random.seed()
    tokenizedMessage.remove("!roll")
    errorMessage = "Format: '!roll AdB...' where A is the number of rolls of a B-sided dice. Up to 6 types at a time, 5 rolls each."
    dieList = tokenizedMessage
    if((''.join(dieList).translate(str.maketrans('0123456789d','           '))).strip() != ''):
        return errorMessage
    rollTotal = 0
    rollText = "Result of rolls :"

    for die in dieList:
        attempt = die.split('d')
        if(len(attempt)!=2):
            return errorMessage
        elif((int(attempt[0]) == 0) or (int(attempt[1]) == 0)):
            return errorMessage
        rollText += " ("
        #attempt = list(die)
        for i in range(int(attempt[0])):
             x = random.randrange(int(attempt[1])) + 1
             rollTotal += x
             if(i == (int(attempt[0]) - 1)):
                rollText += str(x)
             else:
                rollText += (str(x) + " + ")
        rollText += ") +"
    rollText = rollText.strip('+')
    rollText += ("= " + str(rollTotal))

    return rollText


################################################################################
# functionSwitcher
#
# Checks if a message is a valid function, if not it tries to parse it as a
# callback
#
# Args:
#
#   tokenizedMessage - a tokenized version of the message
#
#   message - the original message, used for metadata like user and channel
#
# Returns - nothing
################################################################################
async def functionSwitcher(tokenizedMessage, message):
    global polls
    if(len(tokenizedMessage) == 0 or message.author == client.user):
        return
    functionName = tokenizedMessage[0];

    functionOptions = {
        "!markov": markov,
        "!magic": magic,
        "!poll": createPoll,
        "!roll": roll,
    }

    if(functionName in functionOptions.keys()):
        sent_message = await client.send_message(message.channel, functionOptions[functionName](tokenizedMessage, message))
        if(functionName == "!poll"):
            polls.append(sent_message)
    else:
        for callback in callbackData:
            if(parseCallbackKey(tokenizedMessage, callback["key"])):
                await parseCallbackResult(tokenizedMessage, message, callback["result"])
                break;

################################################################################
# parseCallbackKey
#
# Parses a message according to the key logic in the callbacks json to see if
# it's a valid callback or not.
#
# Args:
#
#   tokenizedMessage - a tokenized version of the message
#
#   callback - the jsonified callback we're using to parse
#
# Return - truth value of the message when evaluated using the callback
################################################################################
def parseCallbackKey(tokenizedMessage, callback):
    if(list(callback.keys())[0] == "+and"):
        truthValue = True
        for boolCallback in callback["+and"]:
            truthValue = truthValue and parseCallbackKey(tokenizedMessage, boolCallback)
        return truthValue
    elif(list(callback.keys())[0] == "+or"):
        truthValue = False
        for boolCallback in callback["+or"]:
            truthValue = truthValue or parseCallbackKey(tokenizedMessage, boolCallback)
        return truthValue
    else:
        #replace any emoji keys with their actual unicode
        if(list(callback.keys())[0] in emojiDict.keys()):
            callback = {
                emojiDict[list(callback.keys())[0]]: callback[list(callback.keys())[0]]
            }
        if(list(callback.keys())[0] in ' '.join(tokenizedMessage).lower()):
            return callback[list(callback.keys())[0]]
        else:
            return not callback[list(callback.keys())[0]]

    return False

################################################################################
# parseCallbackResult
#
# Processes the list of callback results, turning them into their various actions
# using a dict as a switch statement
#
# Args:
#
#   tokenizedMessage - a tokenized version of the message
#
#   message - the original message, used for metadata like user and channel
#
#   callback - the jsonified callback we're using to parse
#
# Return - nothing
################################################################################
async def parseCallbackResult(tokenizedMessage, message, callback):

    possibleActions = {
        "send_file": send_file,
        "add_reaction": add_reaction,
        "send_message": send_message,
        "do_random": do_random,
        "run_func": run_func,
    }

    for resultEntry in callback:
        resultKey = list(resultEntry.keys())[0]
        if(resultKey in possibleActions):
            await possibleActions[resultKey](tokenizedMessage, message, resultEntry[resultKey])

################################################################################
# send_file
#
# Sends the given file to the given channel
#
# Args:
#
#   tokenizedMessage - a tokenized version of the message
#
#   message - the original message, used for metadata like user and channel
#
#   fileToSend - a string with the path of the file to send
#
# Return - nothing
################################################################################
async def send_file(tokenizedMessage, message, fileToSend):
    await client.send_file(message.channel, fileToSend)

################################################################################
# add_reaction
#
# Adds the given reaction to the given message
#
# Args:
#
#   tokenizedMessage - a tokenized version of the message
#
#   message - the original message, used for metadata like user and channel
#
#   reactionToAdd - a string with the name of the emoji to add, found in
#   emojiDict
#
# Return - nothing
################################################################################
async def add_reaction(tokenizedMessage, message, reactionToAdd):
    global emojiDict
    #replace emoji result with actual unicode
    if(reactionToAdd in emojiDict.keys()):
        await client.add_reaction(message, emojiDict[reactionToAdd])

################################################################################
# send_message
#
# Sends the given message to the given channel
#
# Args:
#
#   tokenizedMessage - a tokenized version of the message
#
#   message - the original message, used for metadata like user and channel
#
#   messageToSend - a string message to send
#
# Return - nothing
################################################################################
async def send_message(tokenizedMessage, message, messageToSend):
    await client.send_message(message.channel, messageToSend)

################################################################################
# do_random
#
# Does a random result in the nested list of callback results
#
# Args:
#
#   tokenizedMessage - a tokenized version of the message
#
#   message - the original message, used for metadata like user and channel
#
#   callbackList - a list of callbacks results to randomize
#
# Return - nothing
################################################################################
async def do_random(tokenizedMessage, message, callbackList):
    random.seed()
    await parseCallbackResult(tokenizedMessage, message, callbackList[random.randrange(len(callbackList))])

################################################################################
# run_func
#
# Runs a function as part of a callback result. Doesn't take any args
# at the moment
#
# Args:
#
#   tokenizedMessage - a tokenized version of the message
#
#   message - the original message, used for metadata like user and channel
#
#   functionToRun - the function you want to run for the callback
#
# Return - nothing
################################################################################
async def run_func(tokenizedMessage, message, functionToRun):
    await globals()[functionToRun](tokenizedMessage, message)

################################################################################
# bird_up
#
# Markovs from The Eric Andre Show script file
#
# Args:
#
#   tokenizedMessage - a tokenized version of the message
#
#   message - the original message, used for metadata like user and channel
#
# Return - nothing
################################################################################
async def bird_up(tokenizedMessage, message):
    text_model = markovify.NewlineText(open('./birdup.txt', 'r').read())
    await client.send_message(message.channel, text_model.make_sentence())

################################################################################
# tokenize
#
# Splits a message on spaces unless it includes non-escaped quotes which stop
# splitting until they're closed
#
# Args:
#
#   messageString - a string representation of the message to tokenize
#
# Return - a list of strings for the tokenized message
################################################################################
def tokenize(messageString):
    tokens = []
    currentWord = ""
    inQuotes = False
    lastChar = ''
    escaping = False
    for char in messageString:
        #escape character
        if(char == '\\'):
            if(escaping):
                currentWord += str(char)
            else:
                escaping = True
        #quotes for longer tokens
        elif(char == '"'):
            if (escaping):
                currentWord += str(char)
            else:
                inQuotes = not inQuotes
                if(len(currentWord) > 0):
                    tokens.append(currentWord)
                    currentWord = ""
        #split character
        elif(char == ' '):
            if not(inQuotes):
                if(len(currentWord) > 0):
                    tokens.append(currentWord)
                    currentWord = ""
            else:
                currentWord += str(char)
        else:
            currentWord += str(char)
        #only escape one char
        if(lastChar == '\\'):
            escaping = False
        lastChar = char
    if(len(currentWord) > 0):
        tokens.append(currentWord)
    return tokens

#loads the config
configData = None
configFile = "./config.json"
with open(configFile) as data_file:
    configData = json.load(data_file)

#starts up the client
client.run(configData["token"])
