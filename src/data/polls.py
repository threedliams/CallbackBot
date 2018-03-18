#TODO: handle unicode better instead of just ignoring it
from unidecode import unidecode

import src.data.emoji
import src.app

class Poll:
    def __init__(self, startingText):
        self.content = startingText

################################################################################
# createPoll
#
# Creates and saves a poll given a poll command
#
# Args:
#
#   tokenizedMessage - a tokenized string version of the given message
#
#   message - the original message, used for metadata like the author and channel
#
# Return - the text of the poll to return
################################################################################
def createPoll(message):
    #!poll "this is a poll" "yes" "no"
    messageText = message.tokenizedMessage[1]

    for i in range(2, len(message.tokenizedMessage)):
        if(i-2 > 10):
            break
        messageText += "\n" + src.data.emoji.emojiDict[str(i-2)] + " " + message.tokenizedMessage[i]
        messageText += "\nVotes: none"

    return messageText

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
def addVote(message, reaction, username):
    pollText = message.content
    pollLines = pollText.split("\n")

    for i in range(1, len(pollLines), 2):
        splitLine = pollLines[i].split()

        if(unidecode(reaction.emoji) in src.data.emoji.emojiDict.keys()):
            if(src.data.emoji.emojiDict[unidecode(reaction.emoji)] == splitLine[0] and i + 1 < len(pollLines)):
                if(pollLines[i+1] == "Votes: none"):
                    pollLines [i+1] = "Votes: \"" + username + "\""
                else:
                    pollLines[i+1] += ", \"" + username + "\""
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
def removeVote(message, reaction, username):
    pollText = message.content
    pollLines = pollText.split("\n")

    for i in range(1, len(pollLines), 2):
        splitLine = pollLines[i].split()

        if(unidecode(reaction.emoji) in src.data.emoji.emojiDict.keys()):
            if(src.data.emoji.emojiDict[unidecode(reaction.emoji)] == splitLine[0] and i + 1 < len(pollLines)):
                userList = src.app.tokenize(pollLines[i+1])
                if(len(userList) == 2):
                    pollLines[i+1] = "Votes: none"
                else:
                    if(userList[1] == "\"" + username + "\","):
                        pollLines[i+1].replace("\"" + username + "\", ", "")
                    else:
                        pollLines[i+1].replace(", \"" + username + "\"", "")

    pollText = "\n".join(pollLines)
    return pollText