import datetime

def _print_timestamp(message):
    """Helper function to print messages with a timestamp."""
    print(f"\n[{datetime.datetime.now().strftime('%H:%M:%S')}] {message}")