# AoE2RecordsParser

## What is it ?

This project (will soon) provides a python library to parse .aoe2records files and extract usefull informations from them. It also provide
json files that describe the records' structure and can be used to write this parser in any other language.

The current work is done on 5.1 HD version and seems to work on 5.2 and 5.3 HD versions of the game.

## Why is it usefull ? What can I make with it ?

Among many possibilities, a records parser could be used to :
- rename aoe2record files according to the game and the player involved, automaticaly
- sort/filter records
- export/import records in database
- mod development


## Why remake what has already been done ?

goto-bus-stop did an awesome job on his recanalyst project. However his parser is written in PHP (bwerk!) and doesn't offer a clean file
structure description for helping other to write it in other languages. Moreover it relies on the position of a lot of redundant bytes
and I feel it shouldn't be this dependant of unsafe information plus it is not yet fully functionnal with newest versions of the game. I
then decided to rewrite this parser in python (better!) providing at the same occasion a clean structure description to anyone and
compatible with 5.1 (current) version of the game.

## What this work is based on ?

- Kobeya and its description of the old mgx files [0]
- Wululoo and its help understanding meaning of a lot of bytes

## Contribution

Feel free to suggest any pull request or give any advice : The more we work on it, the faster it goes !

[0] https://web.archive.org/web/20090215065209/http://members.at.infoseek.co.jp/aocai/mgx_format.html
