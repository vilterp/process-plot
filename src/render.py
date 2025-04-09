import matplotlib.pyplot as plt
import pandas as pd
import time

CSV_FILE = 'metrics.csv'
REFRESH_INTERVAL = 1  # seconds

plt.ion()
fig, ax1 = plt.subplots()
ax2 = ax1.twinx()

line1, = ax1.plot([], [], 'g-', label='CPU %')
line2, = ax2.plot([], [], 'b-', label='Memory (MB)')

ax1.set_xlabel('Time')
ax1.set_ylabel('CPU %', color='g')
ax2.set_ylabel('Memory (MB)', color='b')

while True:
    try:
        df = pd.read_csv(CSV_FILE)
        if len(df) < 2:
            time.sleep(REFRESH_INTERVAL)
            continue

        times = pd.to_datetime(df['timestamp'])
        cpu = df['cpu_percent']
        mem = df['memory_mb']

        line1.set_data(times, cpu)
        line2.set_data(times, mem)

        ax1.relim()
        ax1.autoscale_view()
        ax2.relim()
        ax2.autoscale_view()

        fig.autofmt_xdate()
        plt.pause(REFRESH_INTERVAL)
    except KeyboardInterrupt:
        print("Stopped.")
        break
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(REFRESH_INTERVAL)
