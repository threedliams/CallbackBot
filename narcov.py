import discord
import json
import openai
import os

from src.api.discordAPI import DiscordAPI

#loads the config
configData = None
configFile = "./config.json"
with open(configFile) as data_file:
    configData = json.load(data_file)

apiOptions = {
    "discord": DiscordAPI,
}

openaiKey = os.getenv("OPENAI_API_KEY")
if (openaiKey):
    print("Successfully imported OpenAI API key.")
    openai.api_key = openaiKey
else:
    print("Error pulling OpenAI API key from environment variables. Key may be missing.")

apis = []
#starts up the clients
for apiConfig in configData:
    newAPI = apiOptions[apiConfig["api"]](apiConfig["token"])
    newAPI.run(apiConfig["token"])
    # newAPI.run()
    apis.append(newAPI)