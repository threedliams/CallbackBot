import discord
#TODO: handle unicode better instead of just ignoring it
from unidecode import unidecode

from src.api.base import API
from src.data.messages import Message
import src.data.emoji


class DiscordAPI(API, discord.Client):
    def __init__(self, token):
        super().__init__(token)
        self.apiName = "discord"
        self.voice = None
        self.player = None

    def author(self, payload):
        return payload.author

    def authorName(self, payload):
        return payload.author.name

    def content(self, payload):
        return payload.content

    def messageChannel(self, payload):
        return payload.channel

    def emoji(self, payload):
        return payload.emoji

    def reactionMessage(self, payload):
        return payload.message

    def clientName(self):
        return self.user.name

    def clientID(self):
        return self.user.id

    def clientUser(self):
        return self.user

    def getServers(self):
        return self.servers

    def getVoiceChannels(self, server):
        voice_channels = []
        for channel in self.get_all_channels():
            if channel.server == server and channel.type == discord.ChannelType.voice:
                voice_channels.append(channel)
        return voice_channels

    def serverName(self, server):
        return server.name

    def channels(self, server):
        return server.channels

    def channelName(self, channel):
        return channel.name

    def channelID(self, channel):
        return channel.id

    async def getLogs(self, channel):
        async for log_message in self.logs_from(channel, limit=9999999):
            if not(self.authorName(log_message) in list(self.liveChannelMap[self.channelID(channel)].keys())):
                #TODO: handle username conflicts (discriminator or id)
                self.liveChannelMap[self.channelID(channel)][self.authorName(log_message)] = unidecode(self.content(log_message))
            else:
                self.liveChannelMap[self.channelID(channel)][self.authorName(log_message)] = self.liveChannelMap[self.channelID(channel)][self.authorName(log_message)] + "\n" + unidecode(self.content(log_message))

    async def editMessage(self, message, newContent):
        return await self.edit_message(message, newContent)

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
    async def on_ready(self):
        await API.onReady(self)

    ################################################################################
    # on_message
    #
    # When someone sends a message in a channel with a bot, this function fires
    # so you can process the given message
    #
    # Args:
    #
    #   message - a Message object
    #
    # Returns - nothing
    ################################################################################
    async def on_message(self, message):
        await API.onMessage(self, Message(self, message))

    ################################################################################
    # on_reaction_add
    #
    # When someone adds a reaction in a channel with a bot, this function fires
    # so you can process the given reaction
    #
    # Args:
    #
    #   reaction - a Reaction object
    #
    #   username - the reacting user
    #
    # Returns - nothing
    ################################################################################
    async def on_reaction_add(self, reaction, user):
        await API.onReactionAdd(self, reaction, user.name)

    ################################################################################
    # on_reaction_Remove
    #
    # When someone removes a reaction in a channel with a bot, this function fires
    # so you can process the given reaction
    #
    # Args:
    #
    #   reaction - a Reaction object
    #
    #   username - the reacting user
    #
    # Returns - nothing
    ################################################################################
    async def on_reaction_remove(self, reaction, user):
        await API.onReactionRemove(self, reaction, user.name)

    ################################################################################
    # on_reaction_rlear
    #
    # When someone clears a reaction in a channel with a bot, this function fires
    # so you can process the given reaction
    #
    # Args:
    #
    #   reaction - the Reaction object
    #
    #   username - the reacting user
    #
    # Returns - nothing
    ################################################################################
    async def on_reaction_clear(self, reaction, user):
        await API.onReactionClear(self, reaction, user.name)

    ################################################################################
    # sendFile
    #
    # Sends the given file to the given channel
    #
    # Args:
    #
    #   message - a Message object
    #
    #   fileToSend - a string with the path of the file to send
    #
    # Return - nothing
    ################################################################################
    async def sendFile(self, message, fileToSend):
        await self.send_file(message.payload.channel, fileToSend)

    ################################################################################
    # addReaction
    #s
    # Adds the given reaction to the given message
    #
    # Args:
    #
    #   message - a Message object
    #
    #   reactionToAdd - a string with the name of the emoji to add, found in
    #   emojiDict
    #
    # Return - nothing
    ################################################################################
    async def addReaction(self, message, reactionToAdd):
        global emojiDict
        #replace emoji result with actual unicode
        if(reactionToAdd in src.data.emoji.emojiDict.keys()):
            await self.add_reaction(message.payload, src.data.emoji.emojiDict[reactionToAdd])
            
    ################################################################################
    # sendMessage
    #
    # Sends the given message to the given channel
    #
    # Args:
    #
    #   message - a Message object
    #
    #   messageToSend - a string message to send
    #
    # Return - nothing
    ################################################################################
    async def sendMessage(self, message, messageToSend):
        return await self.send_message(message.channel, messageToSend)
            
    ################################################################################
    # playSong
    #
    # Joins your first voice channel and plays a song
    #
    # Args:
    #
    #   message - a Message object
    #
    #   songToPlay - a url to download and play from youtube
    #
    # Return - nothing
    ################################################################################
    async def playSong(self, message, songToPlay):
        if not self.voice:
            voice_channel = self.getVoiceChannels(message.channel.server)[0]
            self.voice = await self.join_voice_channel(voice_channel)
        if self.player:
            self.player.stop()
        self.player = await self.voice.create_ytdl_player(songToPlay)
        self.player.start()
            
    ################################################################################
    # stopAndDisconnect
    #
    # Stops playing a song and disconnects from the voice channel
    #
    # Args:
    #
    #   message - a Message object
    #
    # Return - nothing
    ################################################################################
    async def stopAndDisconnect(self, message):
        if self.voice:
            if self.player:
                self.player.stop()
            if self.voice.is_connected():
                await self.voice.disconnect()
            self.voice = None
            self.player = None
