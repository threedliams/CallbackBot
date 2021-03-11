import markovify
import random

import src.app
import src.data.polls
import src.data.emoji
import src.data.polls
import src.data.messages

#TODO: refactor into a function switch instead of an if block
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
    elif(list(callback.keys())[0] == "+fuzzy"):
        return parseFuzzyKey(tokenizedMessage, callback["+fuzzy"])
    else:
        #replace any emoji keys with their actual unicode
        if(list(callback.keys())[0] in src.data.emoji.emojiDict.keys()):
            callback = {
                src.data.emoji.emojiDict[list(callback.keys())[0]]: callback[list(callback.keys())[0]]
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
#   message - a Message object
#
#   callback - the jsonified callback we're using to parse
#
# Return - nothing
################################################################################
async def parseCallbackResult(message, callback):

    possibleActions = {
        "send_file": message.api.sendFile,
        "add_reaction": message.api.addReaction,
        "send_message": message.api.sendMessage,
        "do_random": do_random,
        "run_func": run_func,
    }

    for resultEntry in callback:
        resultKey = list(resultEntry.keys())[0]
        if(resultKey in possibleActions):
            await possibleActions[resultKey](message, resultEntry[resultKey])

################################################################################
# parseFuzzyKey
#
# Parses a fuzzy callback to try to match.
#
# Args:
#
#   tokenizedMessage - a tokenized version of the message
#
#   callback - the jsonified callback we're using to parse
#
# Return - whether or not the message passes the threshold
################################################################################
def parseFuzzyKey(tokenizedMessage, callback):
    if ("function" in list(callback.keys())):
       return src.app.fuzzyMatch(" ".join(tokenizedMessage), callback["match"], int(callback["threshold"]), callback["function"])

    return src.app.fuzzyMatch(" ".join(tokenizedMessage), callback["match"], int(callback["threshold"]))

################################################################################
# do_random
#
# Does a random result in the nested list of callback results
#
# Args:
#
#   message - a Message object
#
#   callbackList - a list of callbacks results to randomize
#
# Return - nothing
################################################################################
async def do_random(message, callbackList):
    random.seed()
    await parseCallbackResult(message, callbackList[random.randrange(len(callbackList))])

################################################################################
# run_func
#
# Runs a function as part of a callback result. Doesn't take any args
# at the moment
#
# Args:
#
#   message - a Message object
#
#   functionToRun - the function you want to run for the callback
#
# Return - nothing
################################################################################
async def run_func(message, functionToRun):
    await globals()[functionToRun](message)

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
async def bird_up(message):
    text_model = markovify.NewlineText(message.api.birdUpText)
    await message.api.send_message(message.channel, text_model.make_sentence())

################################################################################
# functionSwitcher
#
# Checks if a message is a valid function, if not it tries to parse it as a
# callback
#
# Args:
#
#   message - a Message object
#
# Returns - nothing
################################################################################
async def functionSwitcher(message):
    tokenizedMessage = message.tokenizedMessage
    if(len(tokenizedMessage) == 0 or message.author == message.clientUser):
        return
    functionName = tokenizedMessage[0]

    functionOptions = {
        "!markov": src.app.markov,
        "!magic": src.app.magic,
        "!poll": src.data.polls.createPoll,
        "!roll": src.app.roll,
    }

    if(functionName in functionOptions.keys()):
        sent_message = await message.api.sendMessage(message, functionOptions[functionName](message))
        sent_message = src.data.messages.Message(message.api, sent_message)
        if(functionName == "!poll"):
            message.api.polls[sent_message.messageID] = src.data.polls.Poll(sent_message.content)
    else:
        for callback in message.api.callbackData:
            if(parseCallbackKey(tokenizedMessage, callback["key"])):
                await parseCallbackResult(message, callback["result"])
                break