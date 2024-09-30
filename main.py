"""This module serves as the main entry point for the Telegram bot application.

It handles the initialization of the bot, sets up scheduled tasks for sending messages and media,
and manages user interactions. The module integrates with the worker functions to perform various
tasks such as sending greetings, media items, and reminders, while utilizing the APScheduler for
task scheduling.
"""

import asyncio
from configparser import ConfigParser, ExtendedInterpolation

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telethon import TelegramClient, events
from telethon.tl.custom.message import Message

from src import worker

config = ConfigParser(interpolation=ExtendedInterpolation())
config.read("config.ini")

client = TelegramClient(
    "src/data/bot", config.get("Telegram", "api_id"), config.get("Telegram", "api_hash")
).start()
print("Telegram user bot is now running...")


@client.on(events.NewMessage("me", pattern="/health"))
async def handle_health(event: Message | events.NewMessage):
    """Handles the /health command and responds with the application's health status.

    This asynchronous function listens for messages containing the /health command and replies with
    the current health status of the application. It provides a simple way for users to check if the
    bot is operational.

    Args:
        event (Message | events.NewMessage): The event object representing the incoming message.

    Raises:
        Exception: If there is an error while sending the reply.
    """
    await event.reply(worker.health())


@client.on(events.NewMessage("me", pattern="/greeting_info"))
async def handle_greeting_info(event: Message | events.NewMessage):
    """Handles the /greeting_info command and responds with the next greeting time.

    This asynchronous function listens for messages containing the /greeting_info command and
    replies with the scheduled time for the next greeting. It provides users with information about
    when they can expect the next greeting message.

    Args:
        event (Message | events.NewMessage): The event object representing the incoming message.

    Raises:
        Exception: If there is an error while sending the reply.
    """
    await event.reply(f"Next greeting at {worker.next_greeting_time}")


@client.on(events.NewMessage("me", pattern="/send_greeting"))
async def handle_send_greeting(event: Message | events.NewMessage):
    """Handles the /send_greeting command to send a morning greeting.

    This asynchronous function listens for messages containing the /send_greeting command and
    triggers the sending of a morning greeting via the Telegram client. It then replies to the user
    to confirm that the action has been completed.

    Args:
        event (Message | events.NewMessage): The event object representing the incoming message.

    Raises:
        Exception: If there is an error while sending the greeting or the reply.
    """
    await worker.send_morning_greeting(client)
    await event.reply("Done!")


@client.on(events.NewMessage("me", pattern="/test_greeting"))
async def handle_test_greeting(event: Message | events.NewMessage):
    """Handles the /test_greeting command to send a test morning greeting.

    This asynchronous function listens for messages containing the /test_greeting command and
    triggers the sending of a morning greeting via the Telegram client without marking it as used.
    It then replies to the user to confirm that the action has been completed.

    Args:
        event (Message | events.NewMessage): The event object representing the incoming message.

    Raises:
        Exception: If there is an error while sending the greeting or the reply.
    """
    await worker.send_morning_greeting(client, user_id="me", set_as_used=False)
    await event.reply("Done!")


@client.on(events.NewMessage("me", pattern="/afternoon_media_info"))
async def handle_afternoon_media(event: Message | events.NewMessage):
    """Handles the /afternoon_media_info command and responds with the next media time.

    This asynchronous function listens for messages containing the /afternoon_media_info command
    and replies with the scheduled time for the next afternoon media. It provides users with
    information about when they can expect the next media item.

    Args:
        event (Message | events.NewMessage): The event object representing the incoming message.

    Raises:
        Exception: If there is an error while sending the reply.
    """
    await event.reply(f"Next greeting at {worker.next_afternoon_media_time}")


@client.on(events.NewMessage("me", pattern="/send_afternoon_media"))
async def handle_send_afternoon_media(event: Message | events.NewMessage):
    """Handles the /send_afternoon_media command to send an afternoon media item.

    This asynchronous function listens for messages containing the /send_afternoon_media command
    and triggers the sending of an afternoon media item via the Telegram client. It then replies to
    the user to confirm that the action has been completed.

    Args:
        event (Message | events.NewMessage): The event object representing the incoming message.

    Raises:
        Exception: If there is an error while sending the media or the reply.
    """
    await worker.send_afternoon_media(client)
    await event.reply("Done!")


@client.on(events.NewMessage("me", pattern="/test_afternoon_media"))
async def handle_test_afternoon_media(event: Message | events.NewMessage):
    """Handles the /test_afternoon_media command to send a test afternoon media item.

    This asynchronous function listens for messages containing the /test_afternoon_media command
    and triggers the sending of an afternoon media item via the Telegram client without marking it
    as used. It then replies to the user to confirm that the action has been completed.

    Args:
        event (Message | events.NewMessage): The event object representing the incoming message.

    Raises:
        Exception: If there is an error while sending the media or the reply.
    """
    await worker.send_afternoon_media(client, user_id="me", set_as_used=False)
    await event.reply("Done!")


@client.on(events.NewMessage("me", pattern="/stats"))
async def handle_stats(event: Message | events.NewMessage):
    """Handles the /stats command to send statistics to the user.

    This asynchronous function listens for messages containing the /stats command and triggers the
    sending of statistics related to the application via the Telegram client. It provides users with
    insights into the current state of the application.

    Args:
        event (Message | events.NewMessage): The event object representing the incoming message.

    Raises:
        Exception: If there is an error while sending the statistics.
    """
    await worker.send_stats(client, user_id="me")


async def main():
    """Main entry point for starting the Telegram bot and scheduling tasks.

    This asynchronous function initializes the scheduler and starts the various tasks for sending
    morning greetings, afternoon media, and pill reminders. It then enters an infinite loop to keep
    the application running and responsive.
    """
    scheduler = AsyncIOScheduler()
    worker.start_sending_morning_greeting(scheduler, client, try_today=True)
    worker.start_sending_afternoon_media(scheduler, client, try_today=True)
    worker.start_sending_pills_reminder(scheduler, client)
    scheduler.start()
    while True:
        await asyncio.sleep(1)


client.loop.run_until_complete(main())
