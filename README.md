# New World Town Mission Tracker

Better than notepad!

_This project is not in active development_

A tool I made to semi-automatically track Town Missions in Amazon's game New World.

![Sample image](https://i.imgur.com/22a1BYb.png)

Please note;
1) The software is made to work with exclusively a resolution of 3840x2160. If you would like to use it and use it a on different resolution, you will have to edit the numbers in [main.py](./main.py) and [recognition.py](./recognition.py)
2) Use at your own risk. New World comes with Easy Anti Cheat by Epic Games, the software makes no attempt to hide itself as I consider it a better version of notepad. How it technically functions is very similar to New World's minimap project.
3) That the software does not make attempts to interact with any other process. It just makes a screenshot of the primary display device when a button combination is pressed. It does not read New World's memory, it is not even aware of the New World process and does not depend on it running. In addition, it also does not simulate actions of any input device (such as keyboard or mouse).

## Installation

Ensure the following software is available on `PATH`:

- Python 3.9+
- [https://github.com/tesseract-ocr/tesseract](https://github.com/tesseract-ocr/tesseract)

Install dependencies;

```shell
pip install pywin32
pip install pyyaml
pip install opencv-python
pip install pytesseract
pip install pynput
```

## Usage

Start the program using Python;

```
python main.py
```

This requires the character position to be displayed on screen, which can be turned on by enabling FPS display.

`ctrl-8` displays the overlay containing all tracked missions
`ctrl-9` displays the overlay containing all raw resources to be acquired, for known recipes only (see [recipes.py](./recipes.py))
`ctrl-0` makes a screenshot and tracks missions in the `boards.yml` file

The software will emit a warning log when it does not recognize a mission type, or when it does not recognize a material. It will keep track of materials it does not understand as a gatherable raw material.
