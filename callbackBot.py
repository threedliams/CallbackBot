import discord
import json


from src.api.discordAPI import DiscordAPI


#loads the config
configData = None
configFile = "./config.json"
with open(configFile) as data_file:
    configData = json.load(data_file)

apiOptions = {
    "discord": DiscordAPI,
}

apis = []
#starts up the clients
for apiConfig in configData:
    newAPI = apiOptions[apiConfig["api"]](apiConfig["token"])
    newAPI.run(apiConfig["token"])
    # newAPI.run()
    apis.append(newAPI)