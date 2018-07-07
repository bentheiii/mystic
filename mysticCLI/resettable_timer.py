from threading import Thread, Event

class ResettableTimer(Thread):
    def __init__(self, interval, function):
        Thread.__init__(self)
        self.interval = interval
        self.function = function
        self.finished = Event()
        self.next = None

    def cancel(self):
        self.next = 'end'
        self.finished.set()

    def reset(self):
        self.next = 'reset'
        self.finished.set()

    def run(self):
        while True:
            self.next = None
            self.finished.clear()
            self.finished.wait(self.interval)
            if self.next is None:
                self.function()
                break
            elif self.next == 'end':
                break
            elif self.next == 'reset':
                continue
