import queue
import sys

import numpy as np
import sounddevice as sd
import matplotlib.pyplot as plt 

# CLI things
CYAN    = "\033[96m"
BLACK   = '\033[30m'
RED     = '\033[31m'
GREEN   = '\033[32m'
YELLOW  = '\033[33m'
BLUE    = '\033[34m'
MAGENTA = '\033[35m'
CYAN    = '\033[36m'
WHITE   = '\033[37m'
RESET   = "\033[0m"
BOLD    = "\033[1m"
DIM     = "\033[2m"

# config
device = None 
channels = 1 
sample_rate = 44100   
block_size = 1024 # 23 ms delay

audio_queue = queue.Queue()

def process(x):
    "To process audio later"
    return x

def audio_callback(indata, frames, time, status):
    if status:
        print(status, file=sys.stderr)
    audio_queue.put(process(indata.copy()))

def listen_mic() -> None:
    stream = sd.InputStream(
        device = device, 
        channels = channels, 
        samplerate = sample_rate, 
        blocksize = block_size,
        callback = audio_callback
    )

    print(f"{BOLD}{RED}+{RESET} Streaming started, listening to mic...")

    with stream:
        try:
            while True:
                data = audio_queue.get()

                rms = np.sqrt(np.mean(data**2))

                sys.stdout.write(f"\r{BOLD}{RED}?{RESET} RMS Amplitude: {rms:.4f} ")
                sys.stdout.flush()

        except KeyboardInterrupt:
            print(f"\n{BOLD}{RED}!{RESET} Stream stopped")

def play_audio() -> None:
    T = 5.0    
    t = np.linspace(0, T, int(T * sample_rate), endpoint=False) 
    x = np.sin((np.pi) * 440 * t) 

    sd.play(x, sample_rate)
    sd.wait()

def display_ui() -> None:
    print(f"\n{BOLD}{RED}?{RESET} What do you want to do?")
    print(f"  {BOLD}{RED}1{RESET}: Capture mic audio")
    print(f"  {BOLD}{RED}2{RESET}: Play audio")
    print(f"  {BOLD}{RED}q{RESET}: quit app\n")

def pause() -> None:
    input(f"{BOLD}{RED}?{RESET} Press {BOLD}{RED}ENTER{RESET} to continue")

def main() -> None:
    display_ui()
    choice = input(f"{BOLD}{RED}>{RESET} ").strip()

    while choice != "q":
        if choice == "1":
            listen_mic()

        elif choice == "2":
            play_audio()

        else:
            print(f"{BOLD}{RED}!{RESET} Not a right command. Please choose 1, 2, or q.")

        print("")
        pause()
        display_ui()
        choice = input(f"{BOLD}{RED}>{RESET} ").strip()

    print(f"\n{BOLD}{RED}!{RESET} Exiting...")
    sys.exit(0)

if __name__ == "__main__":
    main()