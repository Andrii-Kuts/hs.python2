# Pesun Bot Analyzer

This bot will read data of a telegram chat and analyze the **pesun bot**. This is a bot, where your "pesun" grows/shrinks daily

Author: Andrii Kuts

## Features

- Leaderboard of best users
- Timeline of top 1 users accross the dataset
- Data for individual users, like average growth, frequency, best rating, etc.

## Running

- Make sure you have docker installed
- Give execution permissions for `start.sh` file
- Run it in console: `/start.sh`
- Wait for the app to start. You will get `Pesun Analysis App is ready!` message when it is ready
- Input the path to the archive. Preferably, it should be in the same folder as repo
- Wait for it to parse
    - You might get a warning `⚠️ Note! Found N unknown users`. This means, that you should create a `nicknames.txt` file in your archive folder. Here, in each line, type a username that was printed to the console along with the user that is associated with that username. Example:
    ```
    @username_123 PersonA
    @mr_bebra MrBebra
    @mr_bebra2 MrBebra
    ```
    - After that, delete `cache` folder and run the program again
- If everything goes well, you should get a message: `Dash is running on http://0.0.0.0:8050/`
- Open this link in the browser and enjoy your statistics 🥂

## Dataset Source

Telegram's "export chat history" feature will be used to create an archive, which will act as data source

## Usage

Will be used from console. For now, it will only print the info to the console. In the future, it will act as a base for a telegram bot with similar functionality