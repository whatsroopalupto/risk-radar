"""Optional local news/price scheduler; AIS runs as a separate stream process."""
import argparse
import time
from .db import init_db
from .pipeline.locking import JobBusy, exclusive_job
from .pipeline.orchestrator import run_cycle


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--interval-seconds", type=int, default=900)
    parser.add_argument("--window-hours", type=int, choices=(24, 48, 72), default=24)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    if args.interval_seconds < 60:
        parser.error("interval must be at least 60 seconds")
    init_db()
    with exclusive_job("scheduler"):
        while True:
            try:
                # Monitoring must not switch the dashboard away from a replay.
                result = run_cycle(args.window_hours, update_display=False)
                print(f"Completed run {result.run_id}: {result.extracted} assessments", flush=True)
            except JobBusy:
                print("Ingestion already running; skipped this poll", flush=True)
            except Exception as exc:
                # Source payloads and credential-bearing exception strings stay out of logs.
                print(f"Monitoring cycle failed ({type(exc).__name__}); retry next poll", flush=True)
            if args.once:
                return
            time.sleep(args.interval_seconds)


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, JobBusy):
        pass
