import discord
import asyncio
import xmlrpc.client
from transport import RequestsTransport
from bidict import bidict


client = discord.Client()
fldigi = xmlrpc.client.ServerProxy('http://{}:{}/'.format('127.0.0.1', 7362), transport=RequestsTransport(use_builtin_types=True), allow_none=True)

callsign_dictionary = {
                        "discord_id" : "callsign"
                      }

discord_channel_ids = [00000000000000]

bot_token = 'A Secret'

callsign_bidict = bidict(callsign_dictionary)

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))
    channel = client.get_channel(discord_channel_id)
    modem = fldigi.modem.get_name()
    game = discord.Game(fldigi.modem.get_name())
    await client.change_presence(status=discord.Status.idle, activity=game)
    while True:
        await asyncio.sleep(1)
        text = fldigi.rx.get_data()
        try:
            text = text.decode("utf-8")
        except UnicodeDecodeError:
            print("Invalid Decode")
        if text != '':
            print(text)
            await channel.send(text)
        text2 = text.upper()
        for key in callsign_bidict.inverse:
            if "@"+key in text2:
                await channel.send("<@!"+callsign_bidict.inverse[key]+">")
        if " PING " in " "+text2:
            fldigi.text.add_tx('PONG de KN4VHM (Auto)')
            await client.change_presence(status=discord.Status.dnd)
            fldigi.main.run_macro(7)

        if fldigi.main.get_trx_status() == 'rx':
            await client.change_presence(status=discord.Status.online, activity=game)
        else:
            await client.change_presence(status=discord.Status.dnd, activity=game)
        if fldigi.modem.get_name() != modem:
            game = discord.Game(fldigi.modem.get_name())
            await client.change_presence(status=discord.Status.idle, activity=game)
            modem = fldigi.modem.get_name()
                
@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.channel.id in discord_channel_ids:
        if str(message.author.id) in callsign_bidict:
            callsign = callsign_bidict[str(message.author.id)]
        else:
            print('Invalid User: '+str(message.author.id)+', '+message.author.nick)
            return

        print(callsign+" transmitted.")
        await message.channel.send('Transmitting...')
        fldigi.text.add_tx(message.content + ' de ' + callsign)
        await client.change_presence(status=discord.Status.dnd)
        fldigi.main.run_macro(7)

client.run(bot_token)
