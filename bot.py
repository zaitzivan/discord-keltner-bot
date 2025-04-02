import discord
import yfinance as yf
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

timeframes = {
    "5 minutes": "5m",
    "15 minutes": "15m",
    "30 minutes": "30m",
    "1 hour": "60m"
}

def calculate_keltner_channel(df, length=20, scalar=1.5):
    df['EMA'] = df['Close'].ewm(span=length, adjust=False).mean()
    df['TR'] = df[['High', 'Low', 'Close']].max(axis=1) - df[['High', 'Low', 'Close']].min(axis=1)
    df['ATR'] = df['TR'].ewm(span=length, adjust=False).mean()
    df['Upper'] = df['EMA'] + scalar * df['ATR']
    df['Lower'] = df['EMA'] - scalar * df['ATR']
    return df.iloc[-1]['Upper'], df.iloc[-1]['EMA'], df.iloc[-1]['Lower']

def get_keltner_values(ticker, interval="5m"):
    df = yf.download(ticker, period="7d", interval=interval)
    if df.empty or len(df) < 20:
        return None
    return calculate_keltner_channel(df)

@client.event
async def on_ready():
    print(f'Bot is online as {client.user}')

@client.event
async def on_message(message):
    if message.author.bot:
        return

    if message.content.startswith("!kelt"):
        parts = message.content.split()
        ticker = parts[1].upper() if len(parts) > 1 else "^GSPC"

        response = f"**Keltner Channel Levels for {ticker}:**\n"


        valid_data_found = False
        for label, interval in timeframes.items():
            values = get_keltner_values(ticker, interval)
            if values:
                valid_data_found = True
                top, mid, bot = values
                response += f"**Time frame: {label}**\n"
                response += f"Top Kelt: {round(top, 2)}\n"
                response += f"Middle Kelt: {round(mid, 2)}\n"
                response += f"Bottom Kelt: {round(bot, 2)}\n"
            else:
                response += f"**Time frame: {label}**\nCould not fetch data.\n"

        if not valid_data_found:
            response += "⚠️ Ticker not recognized. Try symbols like `SPY`, `AAPL`, or `^GSPC`."

        await message.channel.send(response)

client.run(DISCORD_BOT_TOKEN)
