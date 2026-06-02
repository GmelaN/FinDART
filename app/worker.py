import argparse
import time

from app.db.session import SessionLocal
from app.services.worker import run_once


def main() -> None:
    parser = argparse.ArgumentParser(description="finDART DB-backed worker")
    parser.add_argument("command", choices=["run-once", "run"], help="Worker mode")
    parser.add_argument("--sleep", type=float, default=5.0, help="Sleep seconds between polling attempts")
    args = parser.parse_args()

    if args.command == "run-once":
        with SessionLocal() as db:
            job = run_once(db)
            print("No queued job." if job is None else f"{job.job_id} {job.status}")
        return

    while True:
        with SessionLocal() as db:
            job = run_once(db)
            if job is not None:
                print(f"{job.job_id} {job.status}")
        time.sleep(args.sleep)


if __name__ == "__main__":
    main()

