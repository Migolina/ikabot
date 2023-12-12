import random
import time

def wait_random_minutes():
    """ Wait for a random amount of time between 1 and 3 minutes. """
    minutes = random.randint(45, 80)
    time.sleep(minutes * 60)