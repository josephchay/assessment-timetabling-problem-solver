def format_elapsed_time(elapsed_ms: int) -> str:
    """Format milliseconds into minutes, seconds, and milliseconds"""
    total_seconds = elapsed_ms / 1000
    minutes = int(total_seconds // 60)
    seconds = total_seconds % 60

    if seconds >= 1:
        return f"{minutes}m {seconds:.0f}s"
    else:
        return f"{minutes}m {seconds:.3f}s"
