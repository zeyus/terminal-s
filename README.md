Terminal S
==========

A super simple serial terminal with [about 200 lines of Python code](terminal_s/terminal.py)

![](https://user-images.githubusercontent.com/948283/82290238-050e5600-99d9-11ea-9b36-50fb12471e95.png)


## Features

+ auto-detect serial port
+ list available ports to choose
+ loopback device for testing
+ interactive config / connection (default, can be used in Windows Terminal / console app)
+ script mode for non-interactive connection config
+ SIGQUIT (*nix `CTRL + \\`) / SIGBREAK (windows `CTRL + Pause/Break`) detection (useful for non-US keyboard layout)


## Install
```
pip install terminal-s
```

## Run
```
terminal-s
```

On windows, you can also type <kbd>Win</kbd> + <kbd>r</kbd> and enter `terminal-s` to launch it.

```
Options:
  -p, --port TEXT               serial port name
  -b, --baudrate INTEGER RANGE  set baud reate  [0<=x<=115200]
  --parity [N|E|O|S|M]          set parity
  -s, --stopbits INTEGER RANGE  set stop bits  [0<=x<=2]
  -l, --loopback                loopback mode
  -s, --script                  script mode (non-interactive connnection config)
  -e, --enumerate               list available ports
  -h, --help                    Show this message and exit.
```

## Package
```
pip install pyinstaller
pyinstaller terminal-s.spec
```

## C version

The C version is generated using cython, you can replicate it with:

```
pip install cython
cython --embed ./terminal_s/terminal.py
```

### CL

```
cl /O2 ./terminal_s/terminal.c terminal-s.res /I C:\path\to\python\include /link /out:dist/terminal-s.exe "C:\path\to\python\libs\python311.lib
```

### GCC

You can also compile the C version with GCC:

```
gcc -municode -Os -L"/path/to/python/libs" -I"/path/to/python/include" ./terminal_s/terminal.c terminal-s.res -o dist/terminal-s.exe -l"python311"
```
