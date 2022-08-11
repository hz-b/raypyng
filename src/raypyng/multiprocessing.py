
import schwimmbad

class SequentialRunnerPool:
    """Most simplistic implementation of the sequential runner pool
    """
    def map(self,func, opts):
        for item in opts:
            func(item)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass#return Tr

def RunPool(multiprocessing=True):
    """_summary_

    Args:
        multiprocessing (bool or integer, optional): 
        if set to False will use single process sequential runner. 
        if set to True will use multiprocessing code with number of cpu automatically detected
        if set to number will use multiprocessing with number of cpus equal to that number
        Defaults to True.


    Returns:
        _type_: _description_
    """
    if multiprocessing==False:
        return SequentialRunnerPool()
    elif multiprocessing==True:
        multiprocessing==None
    return schwimmbad.JoblibPool(multiprocessing)

# multiprocesing = True/False (autodetect CPU number)
# multiprocessing = 5 # use 5 CPUs