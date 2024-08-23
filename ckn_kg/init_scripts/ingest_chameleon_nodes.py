import requests
from neo4j import GraphDatabase

# Configuration for Neo4j
neo4j_config = {
    'uri': 'bolt://129.114.35.150:7687',
    'user': 'neo4j',
    'password': '#ckn_tacc_neo4j#223#21'
}
NODES_FILE = "./chameleon_node_uids.txt"

# Initialize Neo4j driver
driver = GraphDatabase.driver(neo4j_config['uri'], auth=(neo4j_config['user'], neo4j_config['password']))


# Generate the cypher query per each node_id
def generate_cypher_query(data):
    device_id = data.get('node_name')
    platform = data['architecture'].get('platform_type')
    smp_size = data['architecture'].get('smp_size')
    smt_size = data['architecture'].get('smt_size')
    release_date = data['bios'].get('release_date')
    bios_vendor = data['bios'].get('vendor')
    bios_version = data['bios'].get('version')
    gpu = data['gpu'].get('gpu')
    humanized_ram_size = data['main_memory'].get('humanized_ram_size')
    ram_size = data['main_memory'].get('ram_size')
    device_type = data.get('node_type').replace('_', '-')
    clock_speed = data['processor'].get('clock_speed')
    instruction_set = data['processor'].get('instruction_set')
    processor_model = data['processor'].get('model')
    processor_description = data['processor'].get('other_description')
    processor_vendor = data['processor'].get('vendor')
    processor_version = data['processor'].get('version')

    if ram_size is None:
        ram_size = -1

    query = f"""
    MERGE (device:EdgeDevice {{device_id: "{device_id}"}})
    SET device.platform = "{platform}",
        device.smp_size = {smp_size},
        device.smt_size = {smt_size},
        device.release_date = "{release_date}",
        device.bios_vendor = "{bios_vendor}",
        device.bios_version = "{bios_version}",
        device.gpu = {str(gpu).lower()},
        device.humanized_ram_size = "{humanized_ram_size}",
        device.ram_size = {ram_size},
        device.device_type = "{device_type}",
        device.clock_speed = {clock_speed},
        device.instruction_set = "{instruction_set}",
        device.processor_model = "{processor_model}",
        device.processor_description = "{processor_description}",
        device.processor_vendor = "{processor_vendor}",
        device.processor_version = "{processor_version}",
        device.location = "chameleon",
        device.uid = "{uid}"
    """
    # if gpu exist, add gpu information
    if gpu:
        gpu_info = data['gpu']
        gpu_count = gpu_info.get('gpu_count', 'N/A')
        gpu_model = gpu_info.get('gpu_model', 'N/A')
        gpu_vendor = gpu_info.get('gpu_vendor', 'N/A')

        gpu_portion = f""" ,
        device.gpu_count = "{gpu_count}",
        device.gpu_model = "{gpu_model}",
        device.gpu_vendor = "{gpu_vendor}";
        """

        query = query + gpu_portion
    else:
        query = query + ';'

    return query.strip()


def execute_query_in_neo4j(query):
    with driver.session() as session:
        session.run(query)


# Read the nodes file and process each UID
with open(NODES_FILE, 'r') as file:
    for line in file:
        # Extract UID from the second column
        uid = line.strip().split()[1]
        print(f'Processing {uid} ...')

        # Send GET request to the API
        url = f"https://api.chameleoncloud.org/sites/tacc/clusters/chameleon/nodes/{uid}"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            print(data)
            # Generate the Cypher query
            query = generate_cypher_query(data)

            # Execute the query directly in Neo4j
            execute_query_in_neo4j(query)
        else:
            print(f"Failed to fetch data for UID: {uid}, Status Code: {response.status_code}")

# Close the Neo4j driver
driver.close()
