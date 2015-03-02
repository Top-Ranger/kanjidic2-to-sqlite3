#!/bin/sh

#Remove database if already existing
if [ -e "kanjidb.sqlite3" ]
then
    echo Removing old database
    rm kanjidb.sqlite3
fi

python3 -OO kanjidic2-to-sqlite3.py kanjidic2.xml kanjidb.sqlite3