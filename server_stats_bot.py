import time
import os
import psutil
import discord
import re
from discord.ext import commands, tasks
from systemd import journal
from datetime import datetime, timedelta

TOKEN = 'bot token'  # Replace with your bot token
CHANNEL_ID = channelid  # Replace with the desired channel ID

intents = discord.Intents.default()
intents.typing = False
intents.presences = False
intents.message_content = True

client = discord.Client(intents=intents)

def count_pxe_boots(hours):
    j = journal.Reader()
    since = datetime.now() - timedelta(hours=hours)
    j.seek_realtime(since)
    j.log_level(journal.LOG_INFO)
    j.add_match(_SYSTEMD_UNIT="tftpd-hpa.service")

    ipxe_count = 0
    snponly_count = 0

    for entry in j:
        if 'main.ipxe' in entry['MESSAGE']:
            ipxe_count += 1
        #if 'snponly.efi' in entry['MESSAGE']:
        #    snponly_count += 1

    return ipxe_count, snponly_count


def get_server_stats():
    cpu_percent = psutil.cpu_percent()
    cpu_cores = psutil.cpu_count()
    ram = psutil.virtual_memory()
    uptime = int(psutil.boot_time())
    uptime_days = (time.time() - uptime) / (60 * 60 * 24)
    transfer = psutil.net_io_counters()
    disk = psutil.disk_usage('/')
    hours = 99999  # Adjust the number of hours to look back in the logs
    ipxe_count, snponly_count = count_pxe_boots(hours)


    return {
        'cpu': cpu_percent,
        'cpu_cores': cpu_cores,
        'ram': ram.percent,
        'total_ram': ram.total / (1024 ** 3),  # Convert to GB
        'uptime': uptime_days,
        'disk_total': disk.total / (1024 ** 3),  # Convert to GB
        'disk_used': disk.used / (1024 ** 3),  # Convert to GB
        'ipxe_count': ipxe_count,
        'snponly_count': snponly_count,
        'transfer': {
            'sent_gb': transfer.bytes_sent / (1024 ** 3),  # Convert to GB
            'recv_gb': transfer.bytes_recv / (1024 ** 3)  # Convert to GB
        }
    }

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')
    for guild in client.guilds:
        print(f"Connected to guild: {guild.name} (id: {guild.id})")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.lower().startswith('!dallas stats'):
        print("Received '!dallas stats' command.")
        stats = get_server_stats()

        message_content = (
            f"**CPU usage:** {stats['cpu']}% ({stats['cpu_cores']} cores)\n"
            f"**RAM usage:** {stats['ram']}% (Total: {stats['total_ram']:.2f} GB)\n"
            f"**Uptime:** {stats['uptime']:.2f} days\n"
            f"**iPXE boots:** {stats['ipxe_count']}\n"
            f"**Transfer (GB):** sent={stats['transfer']['sent_gb']:.2f}, received={stats['transfer']['recv_gb']:.2f}\n"
            f"**Disk space:** {stats['disk_used']:.2f} GB used / {stats['disk_total']:.2f} GB total"
        )
        embed = discord.Embed(title = "Server Stats:", description = message_content, color = 0xFF5733)
        embed.set_author (name = "Compudopt", 
        url = "https://www.compudopt.org/",
        icon_url = "https://farm66.staticflickr.com/65535/buddyicons/97042305@N04.jpg?1655313897#97042305@N04")
        await message.channel.send(embed = embed)

client.run(TOKEN)
