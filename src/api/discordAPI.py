import discord
#TODO: handle unicode better instead of just ignoring it
from unidecode import unidecode

from src.api.base import API
from src.data.messages import Message
import src.data.emoji
import youtube_dl


class DiscordAPI(API, discord.Client):
    def __init__(self, token):
        super().__init__(token)
        self.apiName = "discord"
        self.voice = None
        self.player = None
        print("Opus?")
        print(discord.opus.is_loaded())
        discord.opus.load_opus("C:\\ffmpeg\\bin\\opusdec.exe")
        print("Opus?")
        print(discord.opus.is_loaded())


    def author(self, payload):
        return payload.author

    def authorName(self, payload):
        return payload.author.name

    def content(self, payload):
        return payload.content

    def messageChannel(self, payload):
        return payload.channel

    def messageServer(self, payload):
        return payload.guild

    def emoji(self, payload):
        return payload.emoji

    def reactionMessage(self, payload):
        return src.data.messages.Message(self, payload.message)

    def messageID(self, payload):
        return payload.id

    def clientName(self):
        return self.user.name

    def clientID(self):
        return self.user.id

    def clientUser(self):
        return self.user

    def getServers(self):
        return self.guilds

    def getVoiceChannels(self, server):
        return server.voice_channels

    def serverName(self, server):
        return server.name

    def channels(self, server):
        return server.channels

    def channelName(self, channel):
        return channel.name

    def channelID(self, channel):
        return channel.id

    async def getLogs(self, channel):
        async for log_message in channel.history(limit=9999999):
            if not(self.authorName(log_message) in list(self.liveChannelTextMap[self.channelID(channel)].keys())):
                #TODO: handle username conflicts (discriminator or id)
                self.liveChannelTextMap[self.channelID(channel)][self.authorName(log_message)] = unidecode(self.content(log_message))
            else:
                self.liveChannelTextMap[self.channelID(channel)][self.authorName(log_message)] = self.liveChannelTextMap[self.channelID(channel)][self.authorName(log_message)] + "\n" + unidecode(self.content(log_message))

    async def editMessage(self, message, newContent):
        return await message.payload.edit(newContent)

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
        await message.payload.channel.send(file=fileToSend)

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
            await message.payload.add_reaction(src.data.emoji.emojiDict[reactionToAdd])

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
        return await message.channel.send(content=messageToSend)
 
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
            voice_channel = self.getVoiceChannels(message.server)[0]
            self.voice = await voice_channel.connect()
        if self.voice.is_playing():
            self.voice.stop()

        ytdl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                # 'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }

        ffmpeg_options = {
            'options': '-vn'
        }
        with youtube_dl.YoutubeDL(ytdl_opts) as ytdl:
            print("extracting: ")
            info_dict = ytdl.extract_info(songToPlay)
            song = ytdl.prepare_filename(info_dict)
            song = "".join([song.split(".")[0], ".opus"])
            print("done extracting")
        print("attempting to play")
        self.voice.play(discord.FFmpegOpusAudio(song, **ffmpeg_options))
    
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
            if self.voice.is_connected():
                await self.voice.disconnect()
            self.voice = None
