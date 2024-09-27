import subprocess
import time

from jtop import jtop

# Set up logging path and filename
POWER_CSV = "/logs/power.csv"
CONTAINER_NAME = "ckn-daemon"

def convert_memory_to_bytes(mem_str):
    """
    Convert memory string (e.g., '100MiB', '2GiB') to bytes.

    :param mem_str: Memory string
    :return: Memory in bytes as an integer
    """
    mem_str = mem_str.strip()
    if 'GiB' in mem_str:
        return int(float(mem_str.replace('GiB', '').strip()) * (1024 ** 3))  # Convert GiB to bytes
    elif 'MiB' in mem_str:
        return int(float(mem_str.replace('MiB', '').strip()) * (1024 ** 2))  # Convert MiB to bytes
    elif 'KiB' in mem_str:
        return int(float(mem_str.replace('KiB', '').strip()) * 1024)  # Convert KiB to bytes
    elif 'B' in mem_str:
        return int(mem_str.replace('B', '').strip())  # Already in bytes
    else:
        print("Unknown memory format")
        return None


def get_container_cpu_percentage(container_name):
    """
    Get CPU usage percentage for a Docker container using the container name.

    :param container_name: Name or ID of the Docker container
    :return: CPU usage percentage as a float, or None if not found
    """
    try:
        # Run the docker stats command
        result = subprocess.run(
            ['docker', 'stats', container_name, '--no-stream', '--format', '{{.CPUPerc}}'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # Check if the command was successful
        if result.returncode != 0:
            print(f"Error while fetching CPU stats: {result.stderr.decode().strip()}")
            return

        # Get the CPU usage percentage from the output
        cpu_usage = result.stdout.decode('utf-8').strip().replace('%', '')
        return float(cpu_usage)  # Convert to float and return

    except ValueError:
        print("Could not convert CPU usage to float. Check the format of the output.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None
    except subprocess.CalledProcessError as e:
        print(f"Error while fetching CPU stats: {e}")
        return None

def get_container_memory_usage(container_name):
    """
    Get memory usage for a Docker container using the container name.

    :param container_name: Name or ID of the Docker container
    :return: Memory usage in bytes, or None if not found
    """
    try:
        # Run the docker stats command
        result = subprocess.run(
            ['docker', 'stats', container_name, '--no-stream', '--format', '{{.MemUsage}}'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # Check if the command was successful
        if result.returncode != 0:
            print(f"Error while fetching memory stats: {result.stderr.decode().strip()}")
            return None

        # Get the memory usage from the output
        mem_usage = result.stdout.decode('utf-8').strip()

        # Split the output to extract used memory and total memory
        mem_used, mem_total = mem_usage.split('/')  # E.g., "100MiB / 2GiB"

        # Convert used memory to bytes
        return convert_memory_to_bytes(mem_used)

    except ValueError:
        print("Could not parse memory usage. Check the format of the output.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None


def read_stats(jetson):
    """
    Read power stats from jtop and correlate them with CPU/GPU usage of a specific PID.
    """
    # Get power data
    data = jetson.power

    cpu_usage = get_container_cpu_percentage(CONTAINER_NAME)
    memory_usage = get_container_memory_usage(CONTAINER_NAME)

    # Access CPU and GPU power from the correct keys in 'rail'
    if 'POM_5V_CPU' in data['rail'] and 'POM_5V_GPU' in data['rail']:
        cpu_power = round(data['rail']['POM_5V_CPU']['power'] * cpu_usage, 2) # Estimate CPU power for the PID
    else:
        return

    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    # Write data to csv
    with open(POWER_CSV, 'a') as f:
        f.write(f"{timestamp}, {cpu_power}, {cpu_usage}, {memory_usage}, {data['rail']['POM_5V_CPU']['power']}, {data['rail']['POM_5V_GPU']['power']}, {data['tot']['power']}\n")


def jtop_measure():
    """
    Continuously measure power consumption for a specific PID using jtop.
    """
    with jtop() as jetson:
        if jetson.ok():
            while True:
                read_stats(jetson)
                time.sleep(1)  # Log power usage every second


if __name__ == "__main__":
    jtop_measure()
