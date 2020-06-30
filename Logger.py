import logging
import os

formatter = logging.Formatter('%(asctime)s || %(message)s',"%Y-%m-%d %H:%M:%S")

def setup_logger(name, level=logging.CRITICAL):
    handler = logging.FileHandler(name + '.log')
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger

def init_logger(level):
    try:
        if (not os.path.isdir('./log')):
            os.mkdir("log")
        os.chdir("log")

    except Exception as e:
        print("Creation of log directory failed!")
        print("Exception is: " + str(e))

    if level == 0:                          # No Log
        log_level = logging.CRITICAL        # There will be no use of critical tag inside the program

    elif level == 1:                        # Basic Log
        log_level = logging.ERROR           # All the basic stuff will be tagged with this tag

    elif level == 2:                        # Verbose Log
        log_level = logging.WARNING         # Detailes will be tagged with this tag

    else:  # level == 3                     # Extreme Log
        log_level = logging.INFO            # Very low detailes will be tagged with this tag

    logger = setup_logger('logger', log_level)

    os.chdir("..")
    return logger
