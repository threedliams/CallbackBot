import markovify
import re
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import random
import datetime

################################################################################
# attemptMarkovCacheRefresh
#
# Tries to refresh the cache of markov models for each user in each channel.
# Should only refresh the model cache for a user if it has expired (older than
# one hour).
#
# Args:
#
#   api - the object representing the api this request came from
#
#   channelID - the channel ID for the user
#
#   force - set to true to force the cache to refresh even if it hasn't expired
#
# Returns - a markov setence in the form of a quote for the given user
################################################################################
def attemptMarkovCacheRefresh(api, channelID, force=False):
    isSavedReady = api.isSavedReady
    isLiveReady = api.isLiveReady

    usermap = None

    if(isLiveReady):
        usermap = api.liveChannelTextMap[channelID]
    elif(isSavedReady):
        usermap = api.savedChannelTextMap[channelID]
    else:
        return "Sorry, still warming up! Give me a minute. You should only see this message the first time I join a channel."

    if not channelID in api.markovModelCache:
        api.markovModelCache[channelID] = {}

    for username in usermap:
        if not username in api.markovModelCache[channelID]:
            api.markovModelCache[channelID][username] = {}
            api.markovModelCache[channelID][username]['timestamp'] = datetime.datetime.today() - datetime.timedelta(1)
        if force or (api.markovModelCache[channelID][username]['timestamp'] + datetime.timedelta(hours=1) < datetime.datetime.now()):
            api.markovModelCache[channelID][username]['model'] = markovify.NewlineText(usermap[username])
            api.markovModelCache[channelID][username]['timestamp'] = datetime.datetime.now()
   
################################################################################
# getModel
#
# Gets the cached markov model for a given user. If the model is not cached, it
# generates it immediately.
#
# Args:
#
#   api - the object representing the api this request came from
#
#   channelID - the channel ID for the user
#
#   username - the name of the user to get the model from
#
# Returns - a markov setence in the form of a quote for the given user
################################################################################         
def getModel(api, channelID, username):
    if(api.isLiveReady):
        usermap = api.liveChannelTextMap[channelID]
    elif(api.isSavedReady):
        usermap = api.savedChannelTextMap[channelID]
    else:
        return {}

    cached = True
    if not channelID in api.markovModelCache:
        api.markovModelCache[channelID] = {}
        cached = False
    if not username in api.markovModelCache[channelID]:
        api.markovModelCache[channelID][username] = {}
        cached = False

    # Doesn't exist in the cache at all. Expirations are ignored as they'll be updated anyways after the message is generated and sent.
    if cached == False:
        api.markovModelCache[channelID][username]['model'] = markovify.NewlineText(usermap[username])
        api.markovModelCache[channelID][username]['timestamp'] = datetime.datetime.now()

    return api.markovModelCache[channelID][username]['model']

################################################################################
# markov
#
# Generates a markov string for the given user. Supports "me" to markov yourself
# and "everyone" to markov everyone in the channel
#
# Args:
#
#   message - the original message, used for metadata like the author and channel
#
# Returns - a markov setence in the form of a quote for the given user
################################################################################
def markov(message):
    isSavedReady = message.api.isSavedReady
    isLiveReady = message.api.isLiveReady

    #TODO: handle username vs other arguments better
    #TODO: handle users with ' + ' in their name
    usernames = ' '.join(message.tokenizedMessage[1:]).split(' + ')

    usermap = None


    if(isLiveReady):
        usermap = message.api.liveChannelTextMap[message.channelID]
    elif(isSavedReady):
        usermap = message.api.savedChannelTextMap[message.channelID]
    else:
        return "Sorry, still warming up! Give me a minute. You should only see this message the first time I join a channel."

    byUsers = []
    modelsByUser = {}

    for username in usernames:
        if username == "random":
            random.seed()
            randomUser = random.randrange(len(list(usermap.keys())) + 1)
            if randomUser == len(list(usermap.keys())):
                username = "everyone"
            else:
                username = list(usermap.keys())[randomUser]

        if not(username in list(usermap.keys())) and not (username == "everyone" or username == "me"):
            return "Sorry I couldn't find a user named '" + username + "'. Usage: !markov [username]"
        elif username == "everyone":
            for each_username in list(usermap.keys()):
                if each_username == message.clientName:
                    continue
                # compiledLogs = compiledLogs + "\n" + usermap[each_username]
                modelsByUser[each_username] = getModel(message.api, message.channelID, each_username)
            byUsers.append("everyone")
        elif username == "me":
            modelsByUser[message.username] = getModel(message.api, message.channelID, message.username)
            byUsers.append(message.username)
        else:
            modelsByUser[username] = getModel(message.api, message.channelID, username)
            byUsers.append(username)

    # markov_model = markovify.NewlineText(compiledLogs)

    if(len(modelsByUser) > 1):
        markov_model = markovify.combine(list(modelsByUser.values()))
    else:
        markov_model = list(modelsByUser.values())[0]

    newSentence = markov_model.make_sentence()
    #if we couldn't generate a sentence, try a few more times to get a valid one
    if(newSentence is None) or (testForByline(newSentence, message.clientName, usernames, usermap)):
        for i in range(50):
            newSentence = markov_model.make_sentence()
            if not(newSentence is None) and not (testForByline(newSentence, message.clientName, usernames, usermap)):
                break

    byline = ""
    for i in range(len(byUsers)):
        if(i > 0):
            byline += " and "
        byline += byUsers[i]

    if(newSentence is None) or (testForByline(newSentence, message.clientName, usernames, usermap)):
        return "Whoops, I tried a few times but it looks like " + username + " needs to talk more before I can generate a good sentence. Try someone else!"
    else:
        return "\"" + newSentence + "\"\n-" + byline

################################################################################
# testForByline
#
# Checks if a generated message looks like "-user and user and user" in case
# the bot accidentally generates one when you !markov it
#
# Args:
#
#   newSentence - the candidate sentence
#
#   clientName - the bot's name
#
#   usernames - the byline of the message being generated
#
#   usermap - the map of all the users associated with the channel
#
# Return - a string of a randomized response
################################################################################
def testForByline(newSentence, clientName, usernames, usermap):
    if not(newSentence is None):
        if(clientName in usernames or "everyone" in usernames or "random" in usernames):
            #try generating a sentence that isn't like "-user and user and user"
            test_string = newSentence[1:]
            split_test_string = test_string.split(' and ')
            if(len(split_test_string) > 1):
                for split_piece in split_test_string:
                    if not(split_piece in list(usermap.keys())) and not split_piece == "everyone":
                        return False
                return True
    return False

################################################################################
# magic
#
# Generates a random magic 8 ball response
#
# Args:
#
#   message - the original message, used for metadata like the author and channel
#
# Return - a string of a randomized response
################################################################################
def magic(message):
    random.seed()
    magicOptions = ["It is certain", "It is decidedly so", "Without a doubt", "Yes, definitely", "You may rely on it", "As I see it, yes", "Most likely", "Outlook good", "Yes", "Signs point to yes", "Reply hazy try again", "Ask again later", "Better not tell you now", "Cannot predict now", "Concentrate and ask again", "Don't count on it", "My reply is no", "My sources say no", "Outlook not so good", "Very doubtful"]
    magicResult = magicOptions[random.randrange(len(magicOptions))]
    return magicResult

################################################################################
# roll
#
# Generates a list of die rolls (format XdY for X rolls of a Y-sided dice).
# Multiple die types possible per command, separated by space (XdY MdN...)
#
# Args:
#
#   message - the original message, used for metadata like the author and channel
#
# Return - a string of each individual dice result and the sum of all rolls
################################################################################
def roll(message):

    random.seed()
    errorMessage = "Format: '!roll AdB...' where A is the number of rolls of a B-sided dice."

    dieList = message.tokenizedMessage[:]
    dieList.remove("!roll")


    reg = re.compile('[1-9]\d*d[1-9]\d*')
    if(len(list(filter(reg.match,dieList))) != len(dieList)):
        return errorMessage

    rollTotal = 0
    rollText = "Result of rolls:"

    for die in dieList:
        attempt = die.split('d')
        rollText += " ("
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
# fuzzyMatch
#
# Generates a random magic 8 ball response
#
# Args:
#   
#   inputStr - the string to search for
#
#   matchingStr - the string to match against
#
#   threshold - the minimum value for success
#
#   function - the fuzzy matching function to use
#
# Return - True if the ratio passes the threshold, False otherwise
################################################################################
def fuzzyMatch(inputStr, matchingStr, threshold, function="ratio"):
    ratio = 0

    if(function == "ratio"):
        ratio = fuzz.ratio(inputStr, matchingStr)
    elif(function == "token_sort_ratio"):
        ratio = fuzz.token_sort_ratio(inputStr, matchingStr)

    if(ratio >= threshold):
        return True

    return False

################################################################################
# checkForClaps
#
# Runs a fuzzy match against the eric andre transcription to check for a
# reference. If there is a reference, narcov reacts by gently clapping.
#
# Args:
#
#   tokenizedMessage - a tokenized string version of the given message
#
#   message - the original message, used for metadata like the author and channel
#
# Return - None
################################################################################
async def checkForClaps(message):
    #TODO this is super inefficient and should be replaced with something better
    for line in message.api.birdUpText.split('\n'):
        if(fuzzyMatch(message.tokenizedMessage, line, 50)):
            await message.api.addReaction(message, "clap")
            break

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
