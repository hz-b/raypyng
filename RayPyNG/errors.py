
class RayPyError(Exception):
    pass

class RayPyRunnerError(RayPyError):
    pass

class TimeoutError(RayPyError):
    pass