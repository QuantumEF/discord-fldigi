import discord
import asyncio
import xmlrpc.client
from transport import RequestsTransport
from bidict import bidict


client = discord.Client()

#Connect to  the FLDIGI XML-RPC interface
fldigi = xmlrpc.client.ServerProxy('http://{}:{}/'.format('127.0.0.1', 7362), transport=RequestsTransport(use_builtin_types=True), allow_none=True)

#List of authorized users and their corrosponding user id in discord
#(Enable developer mode in discord to copy the user ids they are NOT the "Username#1234" it should be a long number)
callsign_dictionary = {
                          "Discord User ID (As String ie: 00000000)" : "CALLSIGN"
                      }

#This is the channel the bot will read and send messages to and from
discord_channel_id = 00000000000000000

#Bot token
bot_token = 'Your Super Secret Discord Bot Token Here'

#This creates a second dictionary that references "CALLSIGN" : "Discord ID" for easier reference for certain areas
callsign_bidict = bidict(callsign_dictionary)

@client.event
async def on_ready():
        print('We have logged in as {0.user}'.format(client))
        #Sets the channel the bot will send to
        channel = client.get_channel(discord_channel_id) 
        #gets the modem that fldigi is currently in (ie. RTTY, BPSK31, etc)
        modem = fldigi.modem.get_name()
        #Sets the bot user's "game"/status message to the fldigi modem(ie: Playing insert_game_here)
        game = discord.Game(fldigi.modem.get_name())
        await client.change_presence(status=discord.Status.idle, activity=game)
        #Main polling loop (polls about every second)
        while True:
            await asyncio.sleep(1)
            #Gets whatever fldigi that has not been previously pulled (in bytes format)
            text = fldigi.rx.get_data()
            #Try decode the data (ignore giberish messages that contain very obscure characters)
            try:
                text = text.decode("utf-8")
            except UnicodeDecodeError:
                print("Invalid Decode")
                continue
            #Tests to make sure the message does not consist of just newlines, carrige returns, and spaces because discord will throw an empty message error
            if text.strip() != '':
                #Sends message to discord channel and prints it console
                print(text)
                await channel.send(text)
            #Capitalizes the message for some text checks like callsigns
            text2 = text.upper()
            #Looks for if one valid users callsign appears in the message in the format @CALL and Pings/Mentions them 
            for key in callsign_bidict.inverse:
                if "@"+key in text2:
                    await channel.send("<@!"+callsign_bidict.inverse[key]+">")
            #will send a ping response to any message that contains the word PING
            if " PING " in " "+text2:
                #adds text to the fldigi transmit pane, and sets the bot status to dnd
                fldigi.text.add_tx('PONG de KN4VHM (Auto)')
                await client.change_presence(status=discord.Status.dnd)
                #uses a macro to transmit anything that is in the fldigi pane and stop once it all has been transmitted (requires setup in fldigi)
                fldigi.main.run_macro(7)

            #Sets the bot state to online if fldigi is in rx mode otherwise it might be transmitting (can be used to know if the bot threw some sort of error)
            if fldigi.main.get_trx_status() == 'rx':
                await client.change_presence(status=discord.Status.online, activity=game)
            else:
                await client.change_presence(status=discord.Status.dnd, activity=game)
            #If fldigi switched modems change the bots status
            if fldigi.modem.get_name() != modem:
                game = discord.Game(fldigi.modem.get_name())
                await client.change_presence(status=discord.Status.idle, activity=game)
                modem = fldigi.modem.get_name()

@client.event
async def on_message(message):
    #Does not respond to itself
    if message.author == client.user:
        return
    #Only process messages from the given channel
    if message.channel.id == discord_channel_id:
        #Checks if authorized user (While it is automatic control because it is data third party control is allowed, but I dont want that
        if str(message.author.id) in callsign_bidict:
             #Sets the callsign to use when broadcasting the message
            callsign = callsign_bidict[str(message.author.id)]
        else:
            #Logs attempted unauthorized use
            print('Invalid User: '+str(message.author.id)+', '+message.author.nick)
            return
        #Logs use
        print(callsign+" transmitted.")
        #Tells the user it is transmitting
        await message.channel.send('Transmitting...')
        #Adds data to transmit pane
        fldigi.text.add_tx(message.content + ' de ' + callsign)
        #Sets the bots status to indicate it is keying down the radio and transmitting
        await client.change_presence(status=discord.Status.dnd)
        #fldigi macro to transmit the data, and stop once it has transmitted
        fldigi.main.run_macro(7)

client.run(bot_token)
