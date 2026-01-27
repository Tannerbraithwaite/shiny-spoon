#!/usr/bin/env python3
"""
Time Tracker for Course Work
Tracks time spent on courses per night and calculates averages.
Auto-commits to git every 15 minutes.
"""

import json
import os
import subprocess
import time
from datetime import datetime, timedelta
from pathlib import Path
from threading import Thread
from typing import Dict, List, Optional


class TimeTracker:
    def __init__(self, data_file: str = "time_data.json"):
        self.data_file = Path(data_file)
        self.start_time: Optional[datetime] = None
        self.is_running = False
        self.last_commit_time = datetime.now()
        self.commit_interval = timedelta(minutes=15)
        
        # Load existing data
        self.data = self.load_data()
    
    def load_data(self) -> Dict:
        """Load time tracking data from JSON file."""
        if self.data_file.exists():
            try:
                with open(self.data_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {"sessions": [], "last_session": None}
        return {"sessions": [], "last_session": None}
    
    def save_data(self):
        """Save time tracking data to JSON file."""
        with open(self.data_file, 'w') as f:
            json.dump(self.data, f, indent=2, default=str)
    
    def start_session(self):
        """Start tracking time for a session."""
        if self.is_running:
            print("Session is already running!")
            return
        
        self.start_time = datetime.now()
        self.is_running = True
        print(f"Started tracking at {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("Type 'stop' to end the session, or Ctrl+C to exit")
    
    def stop_session(self):
        """Stop tracking time and save the session."""
        if not self.is_running:
            print("No active session to stop!")
            return
        
        if self.start_time is None:
            print("Error: Start time not set!")
            return
        
        end_time = datetime.now()
        duration = end_time - self.start_time
        duration_seconds = int(duration.total_seconds())
        
        # Get the date (night) for this session
        # Consider a "night" as starting from 6 PM to 6 PM next day
        session_date = self.get_night_date(self.start_time)
        
        session_data = {
            "start": self.start_time.isoformat(),
            "end": end_time.isoformat(),
            "duration_seconds": duration_seconds,
            "duration_hours": round(duration_seconds / 3600, 2),
            "date": session_date
        }
        
        self.data["sessions"].append(session_data)
        self.data["last_session"] = session_data
        self.save_data()
        
        print(f"\nSession ended at {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Duration: {self.format_duration(duration_seconds)}")
        print(f"Date (night): {session_date}")
        
        self.is_running = False
        self.start_time = None
    
    def get_night_date(self, dt: datetime) -> str:
        """
        Get the date string for a "night" session.
        A night starts at 6 PM and goes until 6 PM the next day.
        """
        if dt.hour < 18:  # Before 6 PM, it's part of the previous night
            night_date = (dt - timedelta(days=1)).date()
        else:  # After 6 PM, it's part of the current night
            night_date = dt.date()
        return night_date.isoformat()
    
    def format_duration(self, seconds: int) -> str:
        """Format duration in a human-readable way."""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        if hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"
    
    def calculate_statistics(self):
        """Calculate and display statistics."""
        sessions = self.data.get("sessions", [])
        
        if not sessions:
            print("\nNo sessions recorded yet.")
            return
        
        # Calculate total time
        total_seconds = sum(s["duration_seconds"] for s in sessions)
        total_hours = total_seconds / 3600
        
        # Group sessions by night (date)
        nights: Dict[str, List[int]] = {}
        for session in sessions:
            date = session["date"]
            if date not in nights:
                nights[date] = []
            nights[date].append(session["duration_seconds"])
        
        # Calculate per-night totals and averages
        night_totals = {date: sum(durations) for date, durations in nights.items()}
        night_averages = {date: sum(durations) / len(durations) for date, durations in nights.items()}
        
        # Overall average per night
        if nights:
            overall_avg_per_night = sum(night_totals.values()) / len(nights)
        else:
            overall_avg_per_night = 0
        
        # Display statistics
        print("\n" + "="*60)
        print("TIME TRACKING STATISTICS")
        print("="*60)
        print(f"Total sessions: {len(sessions)}")
        print(f"Total time: {self.format_duration(total_seconds)} ({total_hours:.2f} hours)")
        print(f"Total nights tracked: {len(nights)}")
        print(f"Average time per night: {self.format_duration(int(overall_avg_per_night))} ({overall_avg_per_night/3600:.2f} hours)")
        print("\nPer-night breakdown:")
        print("-"*60)
        
        for date in sorted(night_totals.keys(), reverse=True):
            total = night_totals[date]
            avg = night_averages[date]
            count = len(nights[date])
            print(f"{date}: {self.format_duration(int(total))} "
                  f"({count} session{'s' if count != 1 else ''}, "
                  f"avg: {self.format_duration(int(avg))})")
        
        print("="*60)
    
    def git_commit(self):
        """Commit changes to git repository."""
        try:
            # Check if we're in a git repo
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                return  # Not a git repo, skip
            
            # Check if there are changes to commit
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True
            )
            if not result.stdout.strip():
                return  # No changes to commit
            
            # Add all changes
            subprocess.run(
                ["git", "add", "."],
                capture_output=True,
                check=True
            )
            
            # Commit with timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            commit_message = f"Auto-commit: Time tracking update at {timestamp}"
            
            subprocess.run(
                ["git", "commit", "-m", commit_message],
                capture_output=True,
                check=True
            )
            
            # Push to GitHub (or configured remote)
            self.git_push()
            
            print(f"\n[Auto-commit] Committed and pushed changes at {timestamp}")
        except subprocess.CalledProcessError as e:
            print(f"\n[Warning] Git commit failed: {e}")
        except FileNotFoundError:
            pass  # Git not installed, skip
    
    def git_push(self):
        """Push commits to GitHub (or configured remote)."""
        try:
            # Check if there's a remote configured
            result = subprocess.run(
                ["git", "remote", "-v"],
                capture_output=True,
                text=True
            )
            if result.returncode != 0 or not result.stdout.strip():
                print("[Info] No remote repository configured. Skipping push.")
                return
            
            # Get the default branch name (usually 'main' or 'master')
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True,
                text=True
            )
            branch = result.stdout.strip() or "main"
            
            # Get the remote name (usually 'origin')
            result = subprocess.run(
                ["git", "remote"],
                capture_output=True,
                text=True
            )
            remote = result.stdout.strip().split('\n')[0] if result.stdout.strip() else "origin"
            
            # Push to remote
            subprocess.run(
                ["git", "push", remote, branch],
                capture_output=True,
                check=True
            )
            
        except subprocess.CalledProcessError as e:
            print(f"[Warning] Git push failed: {e}")
            print("[Info] Changes are committed locally but not pushed to GitHub.")
        except FileNotFoundError:
            pass  # Git not installed, skip
    
    def check_and_commit(self):
        """Check if it's time to commit and do so if needed."""
        now = datetime.now()
        if now - self.last_commit_time >= self.commit_interval:
            self.git_commit()
            self.last_commit_time = now
    
    def run(self):
        """Main run loop."""
        print("="*60)
        print("COURSE TIME TRACKER")
        print("="*60)
        print("Commands:")
        print("  start  - Start tracking time")
        print("  stop   - Stop tracking and save session")
        print("  stats  - Show statistics")
        print("  quit   - Exit the tracker")
        print("="*60)
        
        # Start auto-commit thread
        commit_thread = Thread(target=self.auto_commit_loop, daemon=True)
        commit_thread.start()
        
        try:
            while True:
                if self.is_running:
                    # Show elapsed time every 30 seconds
                    elapsed = datetime.now() - self.start_time
                    elapsed_seconds = int(elapsed.total_seconds())
                    print(f"\r[Running] Elapsed: {self.format_duration(elapsed_seconds)}", end="", flush=True)
                    time.sleep(1)
                else:
                    command = input("\n> ").strip().lower()
                    
                    if command == "start":
                        self.start_session()
                    elif command == "stop":
                        self.stop_session()
                        self.check_and_commit()
                    elif command == "stats":
                        self.calculate_statistics()
                    elif command == "quit":
                        if self.is_running:
                            print("\nStopping active session...")
                            self.stop_session()
                            self.check_and_commit()
                        print("\nGoodbye!")
                        break
                    else:
                        print("Unknown command. Use 'start', 'stop', 'stats', or 'quit'")
        except KeyboardInterrupt:
            if self.is_running:
                print("\n\nStopping active session...")
                self.stop_session()
                self.check_and_commit()
            print("\nGoodbye!")
    
    def auto_commit_loop(self):
        """Background thread that commits every 15 minutes."""
        while True:
            time.sleep(60)  # Check every minute
            if not self.is_running:
                self.check_and_commit()


def main():
    tracker = TimeTracker()
    tracker.run()


if __name__ == "__main__":
    main()

