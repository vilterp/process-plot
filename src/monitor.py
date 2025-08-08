import psutil
import subprocess
import time
import argparse
import threading
import csv
from datetime import datetime

def write_metrics_to_csv(process, interval, output_file):
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['timestamp', 'cpu_percent', 'memory_mb'])
        while process.is_running():
            try:
                # Get CPU and memory for the main process and all children
                total_cpu = process.cpu_percent(interval=None)
                total_mem = process.memory_info().rss
                
                # Add memory from all child processes recursively
                try:
                    children = process.children(recursive=True)
                    for child in children:
                        try:
                            total_cpu += child.cpu_percent(interval=None)
                            total_mem += child.memory_info().rss
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            continue
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
                
                mem_mb = total_mem / (1024 * 1024)  # Convert to MB
                
                writer.writerow([datetime.now().isoformat(), total_cpu, mem_mb])
                f.flush()
            except psutil.NoSuchProcess:
                break
            time.sleep(interval)

def monitor_process(proc, interval, output_file):
    write_metrics_to_csv(psutil.Process(proc.pid), interval, output_file)

def monitor_process_by_pid(pid, interval, output_file):
    write_metrics_to_csv(psutil.Process(pid), interval, output_file)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', nargs=argparse.REMAINDER, help='Command to run')
    parser.add_argument('--pid', type=int, help='PID of the process to monitor')
    parser.add_argument('--interval', type=float, default=0.1, help='Sampling interval in seconds')
    parser.add_argument('--output', default='metrics.csv', help='CSV file to write metrics to')
    args = parser.parse_args()

    if args.pid:
        monitor_process_by_pid(args.pid, args.interval, args.output)
        print(f"Monitoring complete. Metrics written to {args.output}")
        return

    if not args.command:
        print("You must specify a command to run or a PID to monitor.")
        return

    proc = subprocess.Popen(args.command)
    monitor_thread = threading.Thread(target=monitor_process, args=(proc, args.interval, args.output))
    monitor_thread.start()

    proc.wait()
    monitor_thread.join()
    print(f"Monitoring complete. Metrics written to {args.output}")

if __name__ == '__main__':
    main()
