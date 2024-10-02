# Telegram Auto Texter

Telegram Auto Texter is a Telegram user bot application designed to send automated messages,
greetings, and media at scheduled or random times. The user bot utilizes various features of the
Telegram API to interact with users and provide a seamless experience.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Commands](#commands)
- [Configuration](#configuration)
- [Contributing](#contributing)
- [License](#license)

## Features

- Sends morning and afternoon messages.
- Sends media items based on user-defined schedules.
- Provides reminders for taking pills.
- Customizable greetings and media through YAML configuration files.
- Supports dynamic text generation using tokens.

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/jromero132/telegram-auto-texter.git
    cd telegram-auto-texter```

2. Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3. Obtain your API id and hash and update the [config.ini](config.ini) file.

4. Configure the user bot settings in the file: `src/data/telegram_config.yaml`

## Usage

To run the user bot, execute one of the following command:

- `python -m main`
- `python main.py`

## Commands

- `/health`: Check if the user bot is running.
- `/send_greeting`: Send a morning greeting.
- `/send_afternoon_media`: Send an afternoon media item.
- `/greeting_info`: Get information about the time for the next greeting.
- `/afternoon_media_info`: Get information about the time for the next afternoon media.
- `/test_greeting`: Test sending a morning greeting.
- `/test_afternoon_media`: Test sending an afternoon media item.
- `/stats`: Get statistics about remaining media items.

## Configuration

The user bot's behavior can be customized through YAML configuration files located in the `src/data`
directory. The following files are available:

- [telegram_config.yaml](src/data/telegram_config.yaml): Contains the user bot's configuration about
users and times.
- [stickers.yaml](src/data/stickers.yaml): Defines the sticker items available for sending.
- [media.yaml](src/data/media.yaml): Defines the media items available for sending.
- [register.yaml](src/data/register.yaml): Keeps track of sent media.

## Contributing
Contributions are welcome! Please open an issue or submit a pull request for any enhancements or bug
fixes.

## License
This project is licensed under the MIT License - see the [license](license) file for details.
