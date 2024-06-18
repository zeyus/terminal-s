"""
Terminal for serial port

Requirement:

    + pyserial
    + colorama
    + py-getch
    + click
"""

import os
if os.name == 'nt':
    os.system('title Terminal S')

from collections import deque
import sys
import signal
import threading

import colorama  # type: ignore
import click
import serial  # type: ignore
from serial.tools import list_ports  # type: ignore
from serial.tools.list_ports_common import ListPortInfo  # type: ignore

# Global flag to indicate CTRL+Pause/Break was detected
g_sigquit_detected = False
SIGQUIT = signal.SIGBREAK if os.name == 'nt' else signal.SIGQUIT  # type: ignore
SIGQUIT_DESC = 'CTRL+Pause/Break' if os.name == 'nt' else 'CTRL+\\'

def signal_handler(signum, frame):
    global g_sigquit_detected
    if signum == SIGQUIT:
        g_sigquit_detected = True
        print(f"{SIGQUIT_DESC} detected!")


def run(port: str, baudrate: int, parity: str = 'N', stopbits: int = 1, loopback: bool = False) -> int:
    try:
        device = serial.Serial(port=port,
                                baudrate=baudrate,
                                bytesize=8,
                                parity=parity,
                                stopbits=stopbits,
                                timeout=0.1)
    except:
        print(f'--- Failed to open {port} ---')
        return 0

    signal.signal(SIGQUIT, signal_handler)
    additional_key = 'Ctrl+] or ' if not loopback else ''
    print(f'--- {port} is connected. Press {additional_key}{SIGQUIT_DESC} to quit ---')
    queue: deque[bytes] = deque()
    def read_input():
        global g_sigquit_detected
        if os.name == 'nt':
            from msvcrt import getch, kbhit
        else:
            import tty
            import termios
            stdin_fd = sys.stdin.fileno()
            tty_attr = termios.tcgetattr(stdin_fd)
            tty.setraw(stdin_fd)
            getch = lambda: sys.stdin.read(1).encode()
            kbhit = lambda: False

        while device.is_open:
            if g_sigquit_detected:
                break
            if loopback:
                ch = device.read(1)
                if not ch:
                    continue
                print(ch.decode(errors='replace'), end='', flush=True)
                queue.append(ch)
                continue

            ch = getch()
            if ch == b'\x1d':                   # 'ctrl + ]' to quit
                break

            if loopback:
                device.write(ch)
                continue

            if ch == b'\x00' or ch == b'\xe0':  # arrow keys' escape sequences
                ch2 = getch()
                esc_dict = { b'H': b'A', b'P': b'B', b'M': b'C', b'K': b'D', b'G': b'H', b'O': b'F' }
                if ch2 in esc_dict:
                    queue.append(b'\x1b[' + esc_dict[ch2])
                else:
                    queue.append(ch + ch2)
            else:  
                queue.append(ch)

        if os.name != 'nt':
            termios.tcsetattr(stdin_fd, termios.TCSADRAIN, tty_attr)

    colorama.init()

    thread = threading.Thread(target=read_input)
    thread.start()
    while thread.is_alive():
        try:
            length = len(queue)
            if length > 0:
                device.write(b''.join(queue.popleft() for _ in range(length)))

            if not loopback:
                line = device.readline()
                if line:
                    print(line.decode(errors='replace'), end='', flush=True)
        except IOError:
            print(f'--- {port} is disconnected ---')
            break

    device.close()
    if thread.is_alive():
        print('--- Press R to reconnect the device, or press Enter to exit ---')
        thread.join()
        if queue and queue[0] in (b'r', b'R'):
            return 1
    return 0


def print_ports(ports: list[ListPortInfo]) -> None:
    print('--- Available Ports ----')
    for i, v in enumerate(ports):
        print(f'---  {i}: {v[0]} {v[2]}')

def get_port_n(ports: list[ListPortInfo], n: int) -> str | None:
    try:
        return ports[n][0]
    except:
        return None
    
def get_port_by_idx(default: int | None = None) -> tuple[str | None, int]:
    ports: list[ListPortInfo] = list_ports.comports()
    port_n: int = 0

    if not ports:
        print('--- No serial port available ---')
        return None, port_n
    if len(ports) == 1:
        port = get_port_n(ports, port_n)
    else:
        print_ports(ports)
        port_n = click.prompt('Enter the number of the port', type=click.IntRange(0, len(ports)-1), default=default)
        try:
            port = get_port_n(ports, port_n)
        except:
            return None, port_n

    return port, port_n

def get_port_by_name(name: str) -> tuple[str | None, int]:
    ports: list[ListPortInfo] = list_ports.comports()
    for i, v in enumerate(ports):
        if v[0] == name:
            return v[0], i
    return None, 0


CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
PARITY_CHOICES = ['N', 'E', 'O', 'S', 'M']

@click.command(context_settings=CONTEXT_SETTINGS)
@click.option('-p', '--port', default=None, type=str, help='serial port name')
@click.option('-b', '--baudrate', default=115200, type=click.IntRange(0, 115200), help='set baud reate')
@click.option('--parity', default='N', type=click.Choice(PARITY_CHOICES), help='set parity')
@click.option('-s', '--stopbits', default=1, type=click.IntRange(0, 2), help='set stop bits')
@click.option('-l', '--loopback', default=False, is_flag=True, help='loopback mode')
@click.option('-s', '--script', default=False, is_flag=True, help='script mode (non-interactive connnection config)')
@click.option('-e', '--enumerate', default=False, is_flag=True, help='list available ports')
def main(port: str | None, baudrate: int, parity: str, stopbits: int, loopback: bool, script: bool, enumerate: bool):
    if enumerate:
        ports: list[ListPortInfo] = list_ports.comports()
        print_ports(ports)
        return
    if port is None:
        if script:
            return
        s_port, port_n = get_port_by_idx()
    else:
        s_port, port_n = get_port_by_name(port)

    if not script:
        while not click.confirm(f'Connecting with {s_port} at {baudrate} baudrate, {parity} parity, {stopbits} stopbits.\nDoes this look correct?', default=True):
            s_port, port_n = get_port_by_idx(port_n)
            baudrate = click.prompt('Enter the baudrate', type=click.IntRange(0, 115200), default=baudrate)
            parity = click.prompt('Enter the parity', type=click.Choice(PARITY_CHOICES), default=parity)
            stopbits = click.prompt('Enter the stop bits', type=click.IntRange(0, 2), default=stopbits)

    if s_port is None:
        return

    while run(s_port, baudrate, parity, stopbits, loopback=loopback):
        pass

if __name__ == "__main__":
    main()
