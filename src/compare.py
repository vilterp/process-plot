import psutil
import subprocess
import time
import argparse
import threading
import csv
from datetime import datetime

def write_metrics_to_csv(process, interval, output_file, command_label, command_start_time):
    with open(output_file, 'a', newline='') as f:
        writer = csv.writer(f)
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
                elapsed_seconds = (datetime.now() - command_start_time).total_seconds()
                
                writer.writerow([elapsed_seconds, total_cpu, mem_mb, command_label])
                f.flush()
            except psutil.NoSuchProcess:
                break
            time.sleep(interval)

def monitor_process(proc, interval, output_file, command_label, command_start_time):
    write_metrics_to_csv(psutil.Process(proc.pid), interval, output_file, command_label, command_start_time)

def main():
    parser = argparse.ArgumentParser(description='Compare memory usage of two commands run serially')
    parser.add_argument('command1', nargs='+', help='First command to run')
    parser.add_argument('--command2', nargs='+', required=True, help='Second command to run')
    parser.add_argument('--interval', type=float, default=0.1, help='Sampling interval in seconds')
    parser.add_argument('--output', default='comparison.csv', help='CSV file to write metrics to')
    parser.add_argument('--label1', default='Command 1', help='Label for first command')
    parser.add_argument('--label2', default='Command 2', help='Label for second command')
    args = parser.parse_args()

    # Initialize CSV file with headers
    with open(args.output, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['seconds_elapsed', 'cpu_percent', 'memory_mb', 'command'])
    
    # Run first command
    print(f"Running {args.label1}: {' '.join(args.command1)}")
    command1_start_time = datetime.now()
    proc1 = subprocess.Popen(args.command1)
    monitor_thread1 = threading.Thread(target=monitor_process, args=(proc1, args.interval, args.output, args.label1, command1_start_time))
    monitor_thread1.start()
    
    proc1.wait()
    monitor_thread1.join()
    print(f"{args.label1} completed")
    
    # Small gap between commands
    time.sleep(0.5)
    
    # Run second command
    print(f"Running {args.label2}: {' '.join(args.command2)}")
    command2_start_time = datetime.now()
    proc2 = subprocess.Popen(args.command2)
    monitor_thread2 = threading.Thread(target=monitor_process, args=(proc2, args.interval, args.output, args.label2, command2_start_time))
    monitor_thread2.start()
    
    proc2.wait()
    monitor_thread2.join()
    print(f"{args.label2} completed")
    
    print(f"Comparison complete. Metrics written to {args.output}")

if __name__ == '__main__':
    main()