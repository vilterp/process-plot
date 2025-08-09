#!/usr/bin/env python3
import psutil
import subprocess
import time
import argparse
import threading
import csv
import os
from datetime import datetime
import uuid
import matplotlib.pyplot as plt
import pandas as pd

def write_metrics_to_csv(process, interval, output_file, command_label=None, command_start_time=None, start_time=None):
    """Write process metrics to CSV file"""
    time_reference = command_start_time if command_start_time else start_time
    
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
                elapsed_seconds = (datetime.now() - time_reference).total_seconds()
                
                if command_label:
                    writer.writerow([elapsed_seconds, total_cpu, mem_mb, command_label])
                else:
                    writer.writerow([datetime.now().isoformat(), total_cpu, mem_mb])
                f.flush()
            except psutil.NoSuchProcess:
                break
            time.sleep(interval)

def monitor_process(proc, interval, output_file, command_label=None, command_start_time=None, start_time=None):
    """Monitor a single process"""
    write_metrics_to_csv(psutil.Process(proc.pid), interval, output_file, command_label, command_start_time, start_time)

def monitor_process_by_pid(pid, interval, output_file):
    """Monitor process by PID"""
    start_time = datetime.now()
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['timestamp', 'cpu_percent', 'memory_mb'])
    write_metrics_to_csv(psutil.Process(pid), interval, output_file, start_time=start_time)

def render_single_plot(csv_file, output_file):
    """Render plot for single process monitoring"""
    df = pd.read_csv(csv_file)
    
    if len(df) < 2:
        print("Not enough data points to create plot.")
        return False
    
    times = pd.to_datetime(df['timestamp'])
    mem = df['memory_mb']
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Convert MB to GB for better readability if values are large
    mem_gb = mem / 1024 if mem.max() > 1000 else mem
    mem_label = 'Memory (GB)' if mem.max() > 1000 else 'Memory (MB)'
    
    ax.plot(times, mem_gb, 'b-', label=mem_label, linewidth=2)
    
    ax.set_xlabel('Timestamp')
    ax.set_ylabel(mem_label, color='b')
    ax.tick_params(axis='y', labelcolor='b')
    
    # Format x-axis dates
    fig.autofmt_xdate()
    
    plt.title('Process Memory Usage')
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close(fig)
    return True

def render_comparison_plot(csv_file, output_file):
    """Render comparison plot for multiple processes"""
    df = pd.read_csv(csv_file)
    
    if len(df) < 2:
        print("Not enough data points to create plot.")
        return False
    
    # Get unique commands
    commands = df['command'].unique()
    
    fig, ax = plt.subplots(figsize=(14, 8))
    
    colors = ['blue', 'red', 'green', 'orange', 'purple']
    
    # Determine if we should use GB based on overall max
    overall_max = df['memory_mb'].max()
    if overall_max > 1000:
        mem_unit = 'GB'
        scale_factor = 1024
    else:
        mem_unit = 'MB'
        scale_factor = 1
    
    for i, command in enumerate(commands):
        command_data = df[df['command'] == command]
        times = command_data['seconds_elapsed']
        mem = command_data['memory_mb']
        
        # Apply consistent scaling across all commands
        mem_values = mem / scale_factor
        
        color = colors[i % len(colors)]
        ax.plot(times, mem_values, color=color, label=command, linewidth=2)
    
    ax.set_xlabel('Time (seconds since process start)')
    ax.set_ylabel(f'Memory ({mem_unit})')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.title('Memory Usage Comparison')
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close(fig)
    return True

def cmd_monitor(args):
    """Monitor a single process"""
    # Generate default output filename if not provided
    if not args.output:
        unique_suffix = str(uuid.uuid4())[:8]
        args.output = f"metrics_{unique_suffix}.csv"
    
    if args.pid:
        monitor_process_by_pid(args.pid, args.interval, args.output)
        print(f"Monitoring complete. Metrics written to {args.output}")
        return

    if not args.command:
        print("You must specify a command to run or a PID to monitor.")
        return

    # Initialize CSV file
    with open(args.output, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['timestamp', 'cpu_percent', 'memory_mb'])

    start_time = datetime.now()
    proc = subprocess.Popen(args.command)
    monitor_thread = threading.Thread(target=monitor_process, args=(proc, args.interval, args.output, None, None, start_time))
    monitor_thread.start()

    proc.wait()
    monitor_thread.join()
    print(f"Monitoring complete. Metrics written to {args.output}")

def cmd_compare(args):
    """Compare two processes run serially"""
    # Generate default output filename if not provided
    if not args.output:
        unique_suffix = str(uuid.uuid4())[:8]
        args.output = f"comparison_{unique_suffix}.csv"
    
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
    
    # Auto-render if requested
    if args.render:
        # Generate plot filename from labels with unique suffix
        safe_label1 = "".join(c for c in args.label1 if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_label2 = "".join(c for c in args.label2 if c.isalnum() or c in (' ', '-', '_')).rstrip()
        unique_suffix = str(uuid.uuid4())[:8]
        plot_filename = f"{safe_label1}_vs_{safe_label2}_{unique_suffix}.png".replace(' ', '_')
        
        if render_comparison_plot(args.output, plot_filename):
            print(f"Comparison plot saved to {plot_filename}")
        else:
            print("Failed to create comparison plot.")

def cmd_render(args):
    """Render plot from CSV data"""
    # Generate default output filename if not provided
    if not args.output:
        unique_suffix = str(uuid.uuid4())[:8]
        base_name = os.path.splitext(os.path.basename(args.input))[0]
        args.output = f"{base_name}_plot_{unique_suffix}.png"
    
    if args.watch:
        print(f"Watch mode: updating plot every 1 second. Press Ctrl+C to stop.")
        try:
            while True:
                if os.path.exists(args.input):
                    # Determine plot type based on CSV format
                    try:
                        df = pd.read_csv(args.input, nrows=1)
                        if len(df) > 0:
                            if 'command' in df.columns:
                                # Comparison plot
                                if render_comparison_plot(args.input, args.output):
                                    print(f"Comparison plot updated: {args.output}")
                                else:
                                    print("Waiting for more data...")
                            else:
                                # Single process plot
                                if render_single_plot(args.input, args.output):
                                    print(f"Plot updated: {args.output}")
                                else:
                                    print("Waiting for more data...")
                        else:
                            print("Waiting for data...")
                    except (pd.errors.EmptyDataError, pd.errors.ParserError):
                        print("Waiting for valid data...")
                else:
                    print(f"Waiting for CSV file: {args.input}")
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nWatch mode stopped.")
    else:
        if not os.path.exists(args.input):
            print(f"Input file {args.input} does not exist.")
            return
        
        # Determine plot type based on CSV format
        df = pd.read_csv(args.input, nrows=1)
        if 'command' in df.columns:
            # Comparison plot
            if render_comparison_plot(args.input, args.output):
                print(f"Comparison plot saved to {args.output}")
            else:
                print("Failed to create comparison plot.")
        else:
            # Single process plot
            if render_single_plot(args.input, args.output):
                print(f"Plot saved to {args.output}")
            else:
                print("Failed to create plot.")

def main():
    parser = argparse.ArgumentParser(description='Process monitoring and plotting tool')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Monitor subcommand
    monitor_parser = subparsers.add_parser('monitor', help='Monitor a single process')
    monitor_parser.add_argument('command', nargs='*', help='Command to run')
    monitor_parser.add_argument('--pid', type=int, help='PID of the process to monitor')
    monitor_parser.add_argument('--interval', type=float, default=0.1, help='Sampling interval in seconds')
    monitor_parser.add_argument('--output', help='CSV file to write metrics to (default: auto-generated with unique suffix)')
    monitor_parser.set_defaults(func=cmd_monitor)
    
    # Compare subcommand
    compare_parser = subparsers.add_parser('compare', help='Compare two processes run serially')
    compare_parser.add_argument('--command1', nargs='+', required=True, help='First command to run')
    compare_parser.add_argument('--command2', nargs='+', required=True, help='Second command to run')
    compare_parser.add_argument('--interval', type=float, default=0.1, help='Sampling interval in seconds')
    compare_parser.add_argument('--output', help='CSV file to write metrics to (default: auto-generated with unique suffix)')
    compare_parser.add_argument('--label1', default='Command 1', help='Label for first command')
    compare_parser.add_argument('--label2', default='Command 2', help='Label for second command')
    compare_parser.add_argument('--render', action='store_true', help='Automatically render plot after comparison')
    compare_parser.set_defaults(func=cmd_compare)
    
    # Render subcommand
    render_parser = subparsers.add_parser('render', help='Render plot from CSV data')
    render_parser.add_argument('--input', default='metrics.csv', help='Input CSV file')
    render_parser.add_argument('--output', help='Output PNG file (default: auto-generated with unique suffix)')
    render_parser.add_argument('--watch', action='store_true', help='Watch mode: continuously update plot every 1 second')
    render_parser.set_defaults(func=cmd_render)
    
    args = parser.parse_args()
    
    if not hasattr(args, 'func'):
        parser.print_help()
        return
    
    args.func(args)

if __name__ == '__main__':
    main()