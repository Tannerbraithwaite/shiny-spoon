# shiny-spoon

A time tracking tool for tracking course work time per night and calculating averages.

## Features

- Track time spent on courses per night
- Calculate average time per night and overall statistics
- Automatic git commits every 15 minutes
- Per-night breakdown of study sessions

## Usage

Run the time tracker script:

```bash
python3 time_tracker.py
```

### Commands

- `start` - Start tracking time for a session
- `stop` - Stop tracking and save the session
- `stats` - Display statistics (total time, averages, per-night breakdown)
- `quit` - Exit the tracker

### How It Works

- A "night" is defined as starting at 6 PM and ending at 6 PM the next day
- Time data is stored in `time_data.json`
- The script automatically commits changes to git every 15 minutes
- Statistics show total time, average per night, and breakdown by date

### Example Session

```
> start
Started tracking at 2024-01-15 19:30:00
Type 'stop' to end the session, or Ctrl+C to exit

[Running] Elapsed: 1h 23m 45s
> stop

Session ended at 2024-01-15 21:00:00
Duration: 1h 30m 0s
Date (night): 2024-01-15

> stats
============================================================
TIME TRACKING STATISTICS
============================================================
Total sessions: 5
Total time: 7h 30m 0s (7.50 hours)
Total nights tracked: 3
Average time per night: 2h 30m 0s (2.50 hours)
...
```

## Requirements

- Python 3.6+
- Git (for auto-commit feature)

All dependencies are part of Python's standard library.
