import json
import os

def read_file(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

def write_file(file_path, content):
    with open(file_path, 'w') as file:
        json.dump(content, file, indent=2)

def main():
    script_dir = os.path.dirname(os.path.realpath(__file__))
    cpu_file_path = os.path.join(script_dir, "cpu.json")
    metadata_file_path = os.path.join(script_dir, "metadata.json")
    volume_mount_path = "/data"

    # Read cpu.json and metadata.json from the script directory
    cpu_data = read_file(cpu_file_path)
    metadata_data = read_file(metadata_file_path)

    # Write cpu.json to the volume
    volume_cpu_file_path = os.path.join(volume_mount_path, "cpu.json")
    write_file(volume_cpu_file_path, cpu_data)

    # Write metadata.json to the volume
    volume_metadata_file_path = os.path.join(volume_mount_path, "metadata.json")
    write_file(volume_metadata_file_path, metadata_data)

    print("Files written to volume.")

if __name__ == "__main__":
    main()
