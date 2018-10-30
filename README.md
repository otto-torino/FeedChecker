# Feed Checker

![image](https://raw.githubusercontent.com/otto-torino/FeedChecker/master/app.png "App")

A PyQt5 application which checks news-please feeds list for bad sources (4XX, 5XX response codes)

## Requirements

- PyQt5
- grequests (`pip install grequests`)

## Features

rsnapshot gui:

- select hjson configuration file
- run the check
- display requests and results in a text field
- report errors
- report success
- it and en locales provided

## Usage

Download the project and then

    $ python feedchecker.py

or make it executable.
