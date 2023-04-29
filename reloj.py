
# Me basé en el reloj mostrado en la siguiente página:
# https://www.daniweb.com/programming/software-development/code/485072/count-seconds-in-the-background-python

import threading
import time

class Reloj(threading.Thread):

    def __init__(self, interval):
        # init the thread
        threading.Thread.__init__(self)
        self.interval = interval  # seconds
        # initial value
        self.value = 0
        # controls the while loop in method run
        self.alive = False

    def run(self):
        self.pausa = False
        self.alive = True
        while self.alive:
            if not self.pausa:
                time.sleep(self.interval)
                # update count value
                self.value += self.interval

    def pausar(self):
        if not self.pausa:
            self.pausa = True
        else:
            self.pausa = False

    def finish(self):
        # stop the while loop in method run
        self.alive = False
        return self.value