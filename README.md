 # *remQte*              ![onoff](https://raw.githubusercontent.com/barfnordsen/remQte/main/docs/img/icon.png) 

Remote Control for Samsung smart TVs newer than 2016.


![screenshot remQte main window](https://raw.githubusercontent.com/barfnordsen/remQte/main/docs/img/screenshot.png)

## Requirements
* python3.9+
* PyQt6
* wakeonlan
* samsungtvws
* ssdpy

## Install

### Linux and co.
```
python -m pip install remQte

remQte
```
### Windows
```
py -m pip install remQte

remQte.exe
```

### Build Python Package from source

```
git clone https://github.com/barfnordsen/remQte.git

cd remQte

python -m build

```
## Features

* Qt6 Gui
* TV discovery using ssdp
* importing Channel_list_[$modelstring].zip files
* Turning TV on using wakeonlan

## Issues and Tipps

Feel free to submit issues and Tipps.

This is my first software project with python and qt so please be patient with me :)



