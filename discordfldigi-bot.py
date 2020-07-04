import discord
import asyncio
import xmlrpc.client
from transport import RequestsTransport

client = discord.Client()
fldigi = xmlrpc.client.ServerProxy('http://{}:{}/'.format('127.0.0.1', 7362), transport=RequestsTransport(use_builtin_types=True), allow_none=True)

channel_id = 123456789 #Your Channel ID

def callback(name):
    print("Hello {}!".format(name))

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))
    channel = client.get_channel(channel_id)
    while True:
        await asyncio.sleep(1)
        text = fldigi.rx.get_data()
        if text != b'':
            await channel.send(text.decode("utf-8"))
        if fldigi.main.get_trx_status() == 'rx':
            await client.change_presence(status=discord.Status.online)
        else:
            await client.change_presence(status=discord.Status.dnd)

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.channel.id == channel_id:
        callsign = 'NOCALL'
        await message.channel.send('Transmitting...')
        fldigi.text.add_tx(message.content + ' de ' + callsign)
        await client.change_presence(status=discord.Status.dnd)
        fldigi.main.run_macro(7) #A Macro needs to be configured to transmit <TX><RX>
        
client.run('Your Discord Bot Token')