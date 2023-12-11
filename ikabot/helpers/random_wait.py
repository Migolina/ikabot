import random
import time

def wait_random_minutes():
    """ Wait for a random amount of time between 1 and 3 minutes. """
    minutes = random.randint(2, 5)  # Randomly choose between 1 and 3 minutes
    print(f"Waiting for {minutes} minute(s)...")
    time.sleep(minutes * 60)  # Convert minutes to seconds and wait