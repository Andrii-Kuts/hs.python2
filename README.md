# Pesun Bot Analyzer

This bot will read data of a telegram chat and analyze the **pesun bot**. This is a bot, where your "pesun" grows/shrinks daily

Author: Andrii Kuts

<b>🖖 Video Link: [link](https://www.youtube.com/watch?v=4U9xrpZEHgo)</b>

## Features

- Leaderboard of best users
- Timeline of top 1 users accross the dataset
- Data for individual users, like average growth, frequency, best rating, etc.

## Preparing Archive

To create analytics for an existing group chat, you first need to export chat history. Visit this link to see how to do that on your machine: [link](https://www.androidpolice.com/telegram-export-chats-groups-channels-images/)

User names in a chat might be different, to what they are in Pesun Bot leaderboards. If you want to fix that, create a `nicknames.txt` file in the root folder of your archive. Here, on each line, type two names separated by a space: name of a user in your export and name of the same user in Pesun Bot leaderbots.

### Example:
```
Andrii KAZINAK
SerpongeSH Vyacheslav
knak bangarxng
Санбок Sanbok
Нікитрюк Нікіта
Demian Unnntillll
```

These lines will map user Andrii to KAZINAK and so on

## Running

- Make sure you have docker installed
- Give execution permissions for `start.sh` file
- Run it in console: `/start.sh`
- Wait for the app to start
- Open the Pesun Analytics Bot on telegram: https://t.me/pesun_analysis_bot
- Send `/import` command and send your group chat export as a zip archive in the next message
- Send `/analytics` command
- You should receive a link to the analytics dashboard. Open it in the browser and enjoy 🥂