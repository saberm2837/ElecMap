import datetime

def log_msg(message):
    """Prints a message with a timestamp."""
    print(f"\n[{datetime.datetime.now().strftime('%H:%M:%S')}] {message}")