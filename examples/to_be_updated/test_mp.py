# multiprocessing tests

from multiprocessing import managers


class Job:
    def __init__(self,*args,**kwargs) -> None:
        pass
    
    def run(self):
        print("Run called")


class RunQueue:
    def __init__(self) -> None:
        pass
    
    def enqueue(self,job):
        pass

    def wait(self,timeout=None):
        pass

options = ['8.8.8.8','8.8.4.4','www.helmholtz-berlin.de','27.123.22.82']



def ftest(*args,**kwargs):
    plist = []
    plist.extend([str(v) for v in args])
    plist.extend([f'{k}={v}' for k,v in kwargs.items()])
    pstr = ', '.join(plist)
    return f'ftest({pstr})'

if __name__ == "__main__":
    runqueue = RunQueue()
    for option in options:
        runqueue.enqueue(Job(options))
    runqueue.wait()

    print(ftest(10,aa=12))