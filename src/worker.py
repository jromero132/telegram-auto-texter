"""This module provides functionality for sending scheduled messages and media via Telegram.

It includes functions for sending morning greetings and afternoon messages, media items, and
reminders, as well as managing the state of sent items. The module utilizes YAML files for
configuration and data storage, and it integrates with the APScheduler for scheduling tasks.
"""

import bisect
import random
from datetime import datetime, timedelta
from pathlib import Path

import yaml
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telethon import TelegramClient
from telethon.tl.types import InputDocument

from src.sentence_generator import morning
from src.utils.random import random_time

DATA_PATH = Path("src/data")
MEDIA_PATH = DATA_PATH / "media"
MEDIA_YAML_PATH = DATA_PATH / "media.yaml"
REGISTER_YAML_PATH = DATA_PATH / "register.yaml"
STICKERS_YAML_PATH = DATA_PATH / "stickers.yaml"
TELEGRAM_CONFIG_PATH = DATA_PATH / "telegram_config.yaml"

next_greeting_time: datetime = datetime.now()
next_afternoon_media_time: datetime = datetime.now()


class CustomYamlDumper(yaml.Dumper):
    """Custom YAML dumper that modifies the indentation behavior.

    This class extends the default YAML dumper to ensure that the indentation is always increased
    for block styles, making the output more readable and consistent. It overrides the
    `increase_indent` method to customize the indentation settings.
    """

    def increase_indent(self, flow=False, *args, **kwargs):
        """Increase the indentation level for YAML output.

        This method modifies the behavior of indentation to ensure that it is not indentless,
        providing a clearer structure in the generated YAML.

        Args:
            flow (bool, optional): Indicates whether the indentation is for flow style. Defaults to
                False.
        """
        return super().increase_indent(flow=flow, indentless=False)


def read_yaml(path: Path, *, encoding: str = "utf-8") -> dict:
    """Reads a YAML file and returns its contents as a dictionary.

    This function loads the specified YAML file from the given path and parses its content into
    a Python dictionary, allowing for easy access to configuration settings.

    Args:
        path (Path): The path to the YAML file to be read.
        encoding (str, optional): The character encoding to use when reading the file. Defaults to
            "utf-8".

    Returns:
        dict: A dictionary containing the contents of the YAML file.

    Raises:
        FileNotFoundError: If the specified YAML file does not exist.
        yaml.YAMLError: If there is an error parsing the YAML file.
    """
    with open(path, encoding=encoding) as f:
        return yaml.safe_load(f)


def save_yaml(data: dict, path: Path, *, encoding: str = "utf-8"):
    """Saves a Python dictionary as a YAML file.

    This function serializes the provided dictionary and writes it to the specified file path
    in YAML format, allowing for easy storage and retrieval of structured data.

    Args:
        data (dict): The Python object to be saved as YAML.
        path (Path): The path to the YAML file where the data will be saved.
        encoding (str, optional): The character encoding to use when writing the file. Defaults to
            "utf-8".
    """
    with open(path, "w", encoding=encoding) as f:
        yaml.dump(data, f, Dumper=CustomYamlDumper)


def filter_by_register(data: dict | list, register: list["int | str"], *, key="uid") -> list:
    """Filters the data to exclude items present in the register.

    This function checks the provided data against a list of identifiers in the register and
    returns a new list containing only those items that are not in the register. It allows for
    flexible filtering based on a specified key.

    Args:
        data (dict | list): The data to be filtered, which can be a dictionary or a list.
        register (list[int | str]): A list of identifiers to filter out from the data.
        key (str, optional): The key used to identify items in the data for filtering. Defaults to
            "uid".

    Returns:
        list: A list of items from the data that are not present in the register.
    """
    _register = set(register)
    return [d for d in data if (d if key is None else d[key]) not in _register]


def text_to_timedelta(text: str) -> timedelta:
    """Converts a text representation of time into a timedelta object.

    This function takes a string formatted as "HH:MM:SS" and converts it into a timedelta object,
    allowing for easy manipulation of time intervals in Python.

    Args:
        text (str): The text representation of time to be parsed.

    Returns:
        timedelta: A timedelta object representing the parsed time.

    Raises:
        ValueError: If the input string is not in the expected format or cannot be converted to
            integers.
    """
    _time: list[int] = [int(x) for x in text.split(":")]
    return timedelta(hours=_time[0], minutes=_time[1], seconds=_time[2])


def get_next_time(tm: timedelta, timespan: timedelta, try_now=False) -> datetime:
    """Calculates the next occurrence of a specified time based on the current time.

    This function determines the next datetime by adding a specified time duration to the current
    time and adjusting it according to the provided time interval. It can optionally consider the
    current time as a starting point for the calculation.

    Args:
        tm (timedelta): The time of day to calculate the next occurrence for.
        timespan (timedelta): The interval to add if the calculated time is in the past.
        try_now (bool, optional): If True, the current time is used as the starting point;
            otherwise, the timespan is added to the current time. Defaults to False.

    Returns:
        datetime: The next occurrence of the specified time as a datetime object.
    """
    now = datetime.now()
    if not try_now:
        now += timespan

    dt = datetime(
        year=now.year,
        month=now.month,
        day=now.day,
        hour=tm.seconds // 3600,
        minute=(tm.seconds % 3600) // 60,
        second=tm.seconds % 60,
    )

    if dt < datetime.now():
        dt += timespan

    return dt


def health() -> str:
    """Returns the health status of the application.

    This function provides a simple check to indicate that the application is running and
    operational. It returns a string message confirming the application's status.

    Returns:
        str: A message indicating that the application is alive.
    """
    return "Alive"


def get_morning_greeting() -> str:
    """Retrieves a morning greeting message.

    This function acts as a wrapper to obtain a good morning greeting from the `morning` module. It
    provides a simple interface to access the greeting functionality.

    Returns:
        str: A morning greeting message.
    """
    return morning.get_morning_greeting()


def get_morning_sticker() -> dict:
    """Retrieves a random morning sticker that has not been sent yet.

    This function reads the list of morning stickers from a YAML file and filters out those that
    have already been sent. It then randomly selects one of the remaining stickers and prepares it
    for use by encoding its file reference.

    Returns:
        dict: A dictionary representing the selected morning sticker,
        including its file reference and other associated data.

    Raises:
        FileNotFoundError: If the specified YAML files cannot be found.
        yaml.YAMLError: If there is an error parsing the YAML files.
        ValueError: If there are no available morning stickers to choose from.
    """
    morning_stickers_sent: list = read_yaml(REGISTER_YAML_PATH).get("morning_stickers", [])
    morning_stickers: list = filter_by_register(
        data=read_yaml(STICKERS_YAML_PATH, encoding="latin-1")["morning_stickers"],
        register=morning_stickers_sent,
    )
    morning_sticker: dict = random.choice(morning_stickers)
    morning_sticker["file_reference"] = morning_sticker["file_reference"].encode("latin-1")
    return morning_sticker


def get_morning_media() -> dict:
    """Retrieves a random morning media item that has not been sent yet.

    This function reads the list of morning media items from a YAML file and filters out those that
    have already been sent. It then randomly selects one of the remaining media items for use.

    Returns:
        dict: A dictionary representing the selected morning media item, including its associated
            data.

    Raises:
        FileNotFoundError: If the specified YAML files cannot be found.
        yaml.YAMLError: If there is an error parsing the YAML files.
        ValueError: If there are no available morning media items to choose from.
    """
    morning_media_sent = read_yaml(REGISTER_YAML_PATH).get("morning_media", [])
    morning_media = filter_by_register(
        data=read_yaml(MEDIA_YAML_PATH)["morning_media"],
        register=morning_media_sent,
    )
    return random.choice(morning_media)


def get_afternoon_media() -> dict:
    """Retrieves a random afternoon media item that has not been sent yet.

    This function reads the list of afternoon media items from a YAML file and filters out those
    that have already been sent. It then randomly selects one of the remaining media items for use.

    Returns:
        dict: A dictionary representing the selected afternoon media item, including its associated
            data.

    Raises:
        FileNotFoundError: If the specified YAML files cannot be found.
        yaml.YAMLError: If there is an error parsing the YAML files.
        ValueError: If there are no available afternoon media items to choose from.
    """
    afternoon_media_sent = read_yaml(REGISTER_YAML_PATH).get("afternoon_media", [])
    afternoon_media = filter_by_register(
        data=read_yaml(MEDIA_YAML_PATH)["afternoon_media"],
        register=afternoon_media_sent,
    )
    return random.choice(afternoon_media)


def set_as_used(entry: str, uid: int, db_yaml: Path):
    """Marks a specified entry as used by adding a unique ID to the register.

    This function updates the register by adding the provided unique ID to the list of used IDs for
    the specified entry. If the number of used IDs matches the total entries in the database, it
    clears the list for that entry.

    Args:
        entry (str): The key in the register that corresponds to the entry being updated.
        uid (int): The unique ID to be marked as used.
        db_yaml (Path): The path to the YAML file containing the database entries.

    Raises:
        FileNotFoundError: If the specified YAML files cannot be found.
        yaml.YAMLError: If there is an error parsing the YAML files.
    """
    register = read_yaml(REGISTER_YAML_PATH)
    if uid not in register[entry]:
        bisect.insort(register[entry], uid)
        data = read_yaml(db_yaml)
        if len(register[entry]) == len(data[entry]):
            register[entry] = []

        save_yaml(register, REGISTER_YAML_PATH)


def set_morning_sticker_as_used(uid: int):
    """Marks a morning sticker as used for a specified unique ID.

    This function updates the register to indicate that the morning sticker has been used by the
    provided unique ID. It calls the `set_as_used` function with the appropriate parameters to
    perform the update.

    Args:
        uid (int): The unique ID to be marked as having used the morning sticker.

    Raises:
        FileNotFoundError: If the specified YAML files cannot be found.
        yaml.YAMLError: If there is an error parsing the YAML files.
    """
    set_as_used("morning_stickers", uid, STICKERS_YAML_PATH)


def set_morning_media_as_used(uid):
    """Marks a morning media item as used for a specified unique ID.

    This function updates the register to indicate that the morning media item has been used by the
    provided unique ID. It calls the `set_as_used` function with the appropriate parameters to
    perform the update.

    Args:
        uid (int): The unique ID to be marked as having used the morning media item.

    Raises:
        FileNotFoundError: If the specified YAML files cannot be found.
        yaml.YAMLError: If there is an error parsing the YAML files.
    """
    set_as_used("morning_media", uid, MEDIA_YAML_PATH)


def set_afternoon_media_as_used(uid):
    """Marks an afternoon media item as used for a specified unique ID.

    This function updates the register to indicate that the afternoon media item has been used by
    the provided unique ID. It calls the `set_as_used` function with the appropriate parameters to
    perform the update.

    Args:
        uid (int): The unique ID to be marked as having used the afternoon media item.

    Raises:
        FileNotFoundError: If the specified YAML files cannot be found.
        yaml.YAMLError: If there is an error parsing the YAML files.
    """
    set_as_used("afternoon_media", uid, MEDIA_YAML_PATH)


async def send_morning_greeting(
    client: TelegramClient, user_id: str = "nathy", set_as_used: bool = True
):
    """Sends a morning greeting message along with a sticker and media to a user.

    This asynchronous function retrieves a morning greeting message, a sticker, and media, then
    sends them to the specified user via a Telegram client. It can also mark the sticker and media
    as used if specified.

    Args:
        client (TelegramClient): The Telegram client used to send messages.
        user_id (str, optional): The identifier for the user to whom the greeting is sent.
            Defaults to "nathy".
        set_as_used (bool, optional): Indicates whether to mark the sticker and media as used after
            sending. Defaults to True.

    Raises:
        FileNotFoundError: If the configuration or media files cannot be found.
        yaml.YAMLError: If there is an error parsing the YAML configuration.
        Exception: If there is an error sending messages through the Telegram client.
    """
    tconfig = read_yaml(TELEGRAM_CONFIG_PATH)
    user_id = tconfig.get(user_id, {}).get("chat_id")

    msg = get_morning_greeting()
    sticker = get_morning_sticker()
    media = get_morning_media()

    await client.send_message(user_id, msg)
    await client.send_message(
        user_id,
        file=InputDocument(
            id=sticker["id"],
            access_hash=sticker["access_hash"],
            file_reference=sticker["file_reference"],
        ),
    )
    await client.send_file(user_id, MEDIA_PATH / media["path"])

    if set_as_used:
        set_morning_sticker_as_used(sticker["uid"])
        set_morning_media_as_used(media["uid"])


def start_sending_morning_greeting(
    scheduler: AsyncIOScheduler, client: TelegramClient, try_today: bool = False
):
    """Schedules the sending of morning greeting messages via Telegram.

    This function retrieves the configured start and end times for morning greetings, calculates a
    random time within that range, and schedules the greeting to be sent using the provided
    scheduler. It can also attempt to send the greeting for today if specified.

    Args:
        scheduler (AsyncIOScheduler): The scheduler instance used to manage scheduled jobs.
        client (TelegramClient): The Telegram client used to send messages.
        try_today (bool, optional): If True, sends the greeting today if the calculated time has not
            passed. Defaults to False.
    """
    tconfig = read_yaml(TELEGRAM_CONFIG_PATH)
    start_time = text_to_timedelta(
        tconfig.get("nathy", {}).get("morning_greeting").get("start_time")
    )
    end_time = text_to_timedelta(tconfig.get("nathy", {}).get("morning_greeting").get("end_time"))
    tm = random_time(start=start_time, end=end_time)
    dt = get_next_time(tm, timedelta(days=1), try_today)

    async def wrap(scheduler, client):
        """Wraps the process of sending a morning greeting and rescheduling it.

        This asynchronous function sends a morning greeting message using the provided Telegram
        client and then schedules the next morning greeting using the specified scheduler. It
        ensures that the greeting process is repeated at the appropriate time.

        Args:
            scheduler: The scheduler instance used to manage the scheduling of jobs.
            client: The Telegram client used to send the greeting message.
        """
        await send_morning_greeting(client)
        start_sending_morning_greeting(scheduler, client)

    global next_greeting_time
    next_greeting_time = dt
    print(f"Next greeting at {dt}")
    scheduler.add_job(wrap, "date", run_date=dt, args=[scheduler, client])


async def send_afternoon_media(client, user_id="nathy", set_as_used=True):
    """Sends an afternoon media item to a specified user.

    This asynchronous function retrieves an afternoon media item and sends it to the specified user
    via a Telegram client. It can also mark the media item as used if specified.

    Args:
        client: The Telegram client used to send the media.
        user_id (str, optional): The identifier for the user to whom the media is sent. Defaults to
            "nathy".
        set_as_used (bool, optional): Indicates whether to mark the media item as used after
            sending. Defaults to True.

    Raises:
        FileNotFoundError: If the configuration or media files cannot be found.
        yaml.YAMLError: If there is an error parsing the YAML configuration.
        Exception: If there is an error sending the media through the Telegram client.
    """
    tconfig = read_yaml(TELEGRAM_CONFIG_PATH)
    user_id = tconfig.get(user_id, {}).get("chat_id")
    media = get_afternoon_media()
    await client.send_file(user_id, MEDIA_PATH / media["path"])
    if set_as_used:
        set_afternoon_media_as_used(media["uid"])


def start_sending_afternoon_media(scheduler, client, try_today=False):
    """Schedules the sending of afternoon media messages via Telegram.

    This function retrieves the configured start and end times for afternoon media, calculates a
    random time within that range, and schedules the media to be sent using the provided scheduler.
    It can also attempt to send the media for today if specified.

    Args:
        scheduler: The scheduler instance used to manage scheduled jobs.
        client: The Telegram client used to send messages.
        try_today (bool, optional): If True, sends the media today if the calculated time has not
            passed. Defaults to False.

    Raises:
        FileNotFoundError: If the configuration files cannot be found.
        yaml.YAMLError: If there is an error parsing the YAML configuration.
    """
    tconfig = read_yaml(TELEGRAM_CONFIG_PATH)
    start_time = text_to_timedelta(
        tconfig.get("nathy", {}).get("afternoon_media").get("start_time")
    )
    end_time = text_to_timedelta(tconfig.get("nathy", {}).get("afternoon_media").get("end_time"))
    tm = random_time(start=start_time, end=end_time)
    dt = get_next_time(tm, timedelta(days=1), try_today)

    async def wrap(scheduler, client):
        """Wraps the process of sending afternoon media and rescheduling it.

        This asynchronous function sends an afternoon media item using the provided Telegram client
        and then schedules the next afternoon media sending using the specified scheduler. It
        ensures that the media sending process is repeated at the appropriate time.

        Args:
            scheduler: The scheduler instance used to manage the scheduling of jobs.
            client: The Telegram client used to send the media item.
        """
        await send_afternoon_media(client)
        start_sending_afternoon_media(scheduler, client)

    global next_afternoon_media_time
    next_afternoon_media_time = dt
    print(f"Next afternoon media at {dt}")
    scheduler.add_job(wrap, "date", run_date=dt, args=[scheduler, client])


async def send_stats(client, user_id):
    """Sends a message containing the remaining media items to a specified user.

    This asynchronous function retrieves the current state of media items and the register,
    calculates the remaining items for each media type, and sends a summary message to the
    specified user via the Telegram client.

    Args:
        client: The Telegram client used to send the message.
        user_id: The identifier for the user to whom the message is sent.

    Raises:
        FileNotFoundError: If the specified YAML files cannot be found.
        yaml.YAMLError: If there is an error parsing the YAML files.
        Exception: If there is an error sending the message through the Telegram client.
    """
    register = read_yaml(REGISTER_YAML_PATH)
    media_data = read_yaml(MEDIA_YAML_PATH)

    msg = "Remaining:"
    for data in (media_data,):
        for field in data:
            msg += f"\n  - {field}: {len(data[field]) - len(register[field])}"

    await client.send_message(user_id, msg)


def start_sending_pills_reminder(scheduler, client):
    """Schedules a daily reminder to take pills for a specified user.

    This function retrieves the user's chat ID and the reminder time from the configuration, then
    sets up a scheduled job to send a reminder message via the Telegram client. The reminder message
    is sent daily at the specified time.

    Args:
        scheduler: The scheduler instance used to manage scheduled jobs.
        client: The Telegram client used to send the reminder message.

    Raises:
        FileNotFoundError: If the configuration file cannot be found.
        yaml.YAMLError: If there is an error parsing the YAML configuration.
        Exception: If there is an error scheduling the job or sending the message.
    """
    tconfig = read_yaml(TELEGRAM_CONFIG_PATH)
    user_id = tconfig.get("nathy", {}).get("chat_id")
    reminder_time = tconfig.get("nathy", {}).get("pills_reminder").get("time").split(":")

    async def wrap(scheduler, client):
        await client.send_message(
            user_id, "💊 Amorcito, recuerda tomarte la píldora a las 10. Te amo ❤️"
        )
        start_sending_pills_reminder(scheduler, client)

    scheduler.add_job(
        wrap,
        "cron",
        hour=reminder_time[0],
        minute=reminder_time[1],
        second=reminder_time[2],
        args=[scheduler, client],
    )
