# Function that takes milliseconds as input and returns a formatted time string
def format_elapsed_time(elapsed_ms: int) -> str:
    """Format milliseconds into minutes, seconds, and milliseconds"""
    # Convert total milliseconds to seconds by dividing by 1000
    total_seconds = elapsed_ms / 1000
    # Calculate whole minutes by integer division of seconds by 60
    minutes = int(total_seconds // 60)
    # Calculate remaining seconds using modulo operator
    seconds = total_seconds % 60

    # Return formatted string - if seconds >= 1, show whole seconds, otherwise show decimal seconds
    return f"{minutes}m {seconds:.0f}s" if seconds >= 1 else f"{minutes}m {seconds:.3f}s"
