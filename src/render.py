import matplotlib.pyplot as plt
import pandas as pd
import argparse
import time
import os

def render_plot(csv_file, output_file):
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
    plt.close(fig)  # Close figure to free memory
    return True

def watch_mode(csv_file, output_file, interval):
    print(f"Watch mode: updating plot every {interval} seconds. Press Ctrl+C to stop.")
    try:
        while True:
            if os.path.exists(csv_file):
                if render_plot(csv_file, output_file):
                    print(f"Plot updated: {output_file}")
                else:
                    print("Waiting for more data...")
            else:
                print(f"Waiting for CSV file: {csv_file}")
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nWatch mode stopped.")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', default='metrics.csv', help='Input CSV file')
    parser.add_argument('--output', default='metrics_plot.png', help='Output PNG file')
    parser.add_argument('--watch', action='store_true', help='Watch mode: continuously update plot')
    parser.add_argument('--interval', type=float, default=2.0, help='Update interval in watch mode (seconds)')
    args = parser.parse_args()
    
    if args.watch:
        watch_mode(args.input, args.output, args.interval)
    else:
        if render_plot(args.input, args.output):
            print(f"Plot saved to {args.output}")
        else:
            print("Failed to create plot.")

if __name__ == '__main__':
    main()
