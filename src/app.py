import markovify
import re
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import random

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
def markov(message):
    isSavedReady = message.api.isSavedReady
    isLiveReady = message.api.isLiveReady

    #TODO: handle username vs other arguments better
    #TODO: handle users with '+' in their name
    usernames = ' '.join(message.tokenizedMessage[1:]).split(' + ')

    usermap = None


    if(isLiveReady):
        usermap = message.api.liveChannelMap[message.channelID]
    elif(isSavedReady):
        usermap = message.api.savedChannelMap[message.channelID]
    else:
        return "Sorry, still warming up! Give me a minute. You should only see this message the first time I join a channel."


    compiledLogs = ""
    byUsers = []

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
                compiledLogs = compiledLogs + "\n" + usermap[each_username]
            byUsers.append("everyone")
        elif username == "me":
            compiledLogs += usermap[message.username]
            byUsers.append(message.username)
        else:
            compiledLogs += usermap[username]
            byUsers.append(username)

    markov_model = markovify.NewlineText(compiledLogs)

    newSentence = markov_model.make_sentence();
    #if we couldn't generate a sentence, try a few more times to get a valid one
    if(newSentence is None):
        for i in range(5):
            newSentence = markov_model.make_sentence();
            if not(newSentence is None):
                break;

    byline = ""
    for i in range(len(byUsers)):
        if(i > 0):
            byline += " and "
        byline += byUsers[i]

    if(newSentence is None):
        return "Whoops, I tried a few times but it looks like " + username + " needs to talk more before I can generate a good sentence. Try someone else!"
    else:
        return "\"" + newSentence + "\"\n-" + byline

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
#   None
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
