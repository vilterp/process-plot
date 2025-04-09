# monitor.py
import psutil
import subprocess
import time
import argparse
import threading
import csv
from datetime import datetime

def monitor_process(proc, interval, output_file):
    pid = proc.pid
    p = psutil.Process(pid)

    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['timestamp', 'cpu_percent', 'memory_mb'])
        while proc.poll() is None:
            try:
                cpu = p.cpu_percent(interval=None)
                mem = p.memory_info().rss / (1024 * 1024)  # MB
                writer.writerow([datetime.now().isoformat(), cpu, mem])
                f.flush()
            except psutil.NoSuchProcess:
                break
            time.sleep(interval)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', nargs=argparse.REMAINDER)
    parser.add_argument('--interval', type=float, default=1.0, help='Sampling interval in seconds')
    parser.add_argument('--output', default='metrics.csv', help='CSV file to write metrics to')
    args = parser.parse_args()

    if not args.command:
        print("You must specify a command to run.")
        return

    proc = subprocess.Popen(args.command)
    monitor_thread = threading.Thread(target=monitor_process, args=(proc, args.interval, args.output))
    monitor_thread.start()

    proc.wait()
    monitor_thread.join()
    print(f"Monitoring complete. Metrics written to {args.output}")

if __name__ == '__main__':
    main()
