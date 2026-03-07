import time
from threading import Thread
import threading


print_lock = threading.Lock()


def remind(text, local_time, repeat):
    for i in range(repeat):
        time.sleep(local_time * 60)
        with print_lock:
            print(text)


flag = 1


def new_remind():
    with print_lock:
        print('new? y/n')
        answer = str(input())
    if answer == 'y':
        print('what?')
        text = str(input())
        print('time?')
        local_time = float(input())
        print('how many times?')
        repeat = int(input())
        thread = Thread(target=remind, args=(text, local_time, repeat))
        thread.start()
    else:
        global flag
        flag = 0


while flag:
    new_remind()
    time.sleep(20)
