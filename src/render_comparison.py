import matplotlib.pyplot as plt
import pandas as pd
import argparse

def render_comparison_plot(csv_file, output_file):
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

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', default='comparison.csv', help='Input CSV file')
    parser.add_argument('--output', default='comparison_plot.png', help='Output PNG file')
    args = parser.parse_args()
    
    if render_comparison_plot(args.input, args.output):
        print(f"Comparison plot saved to {args.output}")
    else:
        print("Failed to create plot.")

if __name__ == '__main__':
    main()