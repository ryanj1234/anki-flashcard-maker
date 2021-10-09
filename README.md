# anki-flashcard-maker
Anki addon which will download definitions and audio from wiktionary and create flashcards from it.

## Install
To install as an anki addon, copy repository to addons folder `C:\Users\%USERNAME%\AppData\Roaming\Anki2\addons21\Ryans Flashcard Maker`

Open the vendor folder from the command line and install dependencies `pip_install_vendor.sh`

## Configure
By default, the program will check for words in a text file named `vocab.txt` on your desktop. This can be changed from the config menu within anki

```
{
    "FILE_NAME": "C:\\Users\\ryanj\\Desktop\\vocab.txt",
    "LANGUAGE": "Russian"
}
```

Right now, language can either be "Russian" or "Spanish".

If you have an API key for forvo, whenever there is no audio found on wiktionary for a word the program will try to download from forvo instead. Add this to a parameter `FORVO_API_KEY`.
```
{
    "FILE_NAME": "C:\\Users\\ryanj\\Desktop\\vocab.txt",
    "LANGUAGE": "Russian",
    "FORVO_API_KEY": "YOUR_API_KEY"
}
```

## Running
From within Anki, select `Tools->Run Card Generator`