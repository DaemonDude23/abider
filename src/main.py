import logging.config
import os
import subprocess
from time import time
from typing import Optional
from typing import Type

import discord
import discordhealthcheck
import yaml

logging_conf = Type[dict]
with open("logging-config.yaml") as f:
    config = yaml.load(f, Loader=yaml.FullLoader)
    logging_conf = logging.config.dictConfig(config)


def get_subprocess_timeout() -> int:
    try:
        if int(os.environ["ABIDER_SUBPROCESS_TIMEOUT"]):
            subprocess_timeout = int(os.environ["ABIDER_SUBPROCESS_TIMEOUT"])
            logging.info(f"Environment variable ABIDER_SUBPROCESS_TIMEOUT set to {subprocess_timeout}s")
            return subprocess_timeout
    except:
        logging.info(f"Environment variable ABIDER_SUBPROCESS_TIMEOUT not found. Defaulting to 60s timeout")
        return 60


def get_discord_channel_id() -> int:
    try:
        if int(os.environ["ABIDER_DISCORD_CHANNEL_ID"]):
            return int(os.environ["ABIDER_DISCORD_CHANNEL_ID"])
    except KeyError:
        logging.fatal(f"Unable to locate required environment variable: ABIDER_DISCORD_CHANNEL_ID")
        exit(1)


def get_abider_weekday() -> bool:
    try:  #  You don't go out looking for a job dressed like that, do ya? On a weekday?
        if os.environ["ABIDER_WEEKDAY"] == "enabled":
            return True
    except:
        return False


# debugpy
try:
    try:
        debugpy_enabled: Optional[str] = os.environ["ABIDER_DEBUGPY"]
        if debugpy_enabled == "enabled":
            import debugpy

            debugpy.listen(("0.0.0.0", 5678))

        debugpy_wait_enabled: Optional[str] = os.environ["ABIDER_DEBUGPY_WAIT"]
        if debugpy_wait_enabled == "enabled":
            debugpy.wait_for_client()
    except KeyError:
        pass
except ImportError:
    pass


def format_monospace(command: str) -> str:
    return f"`{command}`"


def format_monospace_bash(command: str) -> str:
    return f"```bash\n{command}\n```"


def format_text_block(command: str) -> str:
    return f"```\n{command}\n```"


channel_id = get_discord_channel_id()
weekday = get_abider_weekday()
subprocess_timeout = get_subprocess_timeout()


class process_info:
    def __init__(self) -> None:
        self.author: str = str()
        self.command: str = str()
        self.duration: float = float()
        self.returncode: int = int()
        self.stderr: str = str()
        self.stdout: str = str()

    def response_preparer(self) -> object:
        color: object = object
        if self.returncode == 0:
            color = discord.Color.green()
        elif isinstance(self.returncode, int):
            color = discord.Color.red()
        else:
            color = discord.Color.dark_gray()

        embed = discord.Embed(color=color)
        embed.add_field(name="Command", value=format_monospace_bash(self.command), inline=False)
        embed.add_field(name="Issuer", value=self.author, inline=True)
        embed.add_field(name="Duration", value=f"{self.duration}s", inline=True)
        if isinstance(self.returncode, int):
            if self.returncode == 124:
                embed.add_field(name="Return Code", value=f"{self.returncode} (Timeout)", inline=True)
            else:
                embed.add_field(name="Return Code", value=self.returncode, inline=True)
        if self.stderr:
            embed.add_field(name="stderr", value=format_text_block(self.stderr[0:2500]), inline=False)
        if self.stdout:
            embed.add_field(name="stdout", value=format_text_block(self.stdout[0:2500]), inline=False)
        return embed

    def execute_command(self) -> int | float | str | str:
        if weekday:
            logging.info(f"Executing command with timeout of {subprocess_timeout} seconds: '{self.command}'")
        else:
            logging.info(f"Far out... executing command with timeout of {subprocess_timeout} seconds: '{self.command}'")

        self.start_time = time()
        timed_out = False
        try:
            cmd = subprocess.run(
                self.command,
                capture_output=True,
                check=True,
                shell=True,
                text=True,
                timeout=subprocess_timeout,
            )
        except subprocess.CalledProcessError as e:  # command returned an error
            cmd = e
        except subprocess.TimeoutExpired as e:  # detect timeout
            cmd = e
            timed_out = True
        finally:
            self.end_time: float = time()

            # calculate total time spent
            duration: float = self.end_time - self.start_time
            if timed_out:
                return 124, float(duration), str(cmd.stdout), str(cmd.stderr)
            else:
                return cmd.returncode, float(duration), str(cmd.stdout), str(cmd.stderr)


intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents, logging_conf=logging_conf)


@bot.event
async def on_ready() -> None:
    await discordhealthcheck.start(bot)
    logging.info(f"Abider has successfully logged in to discord as {bot.user}")

    # only display startup message if channel ID is provided in env var
    if channel_id > 0:
        channel = bot.get_channel(channel_id)
        hostname: str = os.environ["HOSTNAME"]
        if weekday:
            embed = discord.Embed(title="Abider is online", color=discord.Color.dark_teal())
        else:
            embed = discord.Embed(title="Dude, here!", color=discord.Color.dark_teal())
        embed.add_field(name="Hostname", value=format_monospace(hostname))
        await channel.send(embed=embed)


@bot.event
async def on_message(message: object) -> None:
    if message.author == bot.user:
        return

    if bot.user in message.mentions:
        process_details = process_info()
        process_details.author = message.author.display_name

        # replace the mention of this bot in the content to extract only the command
        process_details.command = message.content.replace(f"{message.mentions[0].mention} ", "")

        if weekday:
            await message.channel.send(
                f"Executing command (timeout {format_monospace(subprocess_timeout)}s): {format_monospace(process_details.command)}"
            )
        else:
            await message.channel.send(f"The Dude abides:\n{format_monospace_bash(process_details.command)}")

        (
            process_details.returncode,
            process_details.duration,
            process_details.stdout,
            process_details.stderr,
        ) = process_details.execute_command()

        process_details.duration = round(process_details.duration, 3)  # round to 3rd decimal
        await message.channel.send(embed=process_details.response_preparer())


if __name__ == "__main__":
    bot.run(os.environ["ABIDER_DISCORD_TOKEN"])
    bot.close()
