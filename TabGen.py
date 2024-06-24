import os
import random
from bitcoinrpc.authproxy import AuthServiceProxy

def load_rpc_credentials(filename):
    """Load RPC credentials from a configuration file."""
    credentials = {}
    with open(filename, 'r') as file:
        for line in file:
            parts = line.strip().split('=')
            if len(parts) == 2:
                credentials[parts[0]] = parts[1]
    return credentials

def get_rpc_connection():
    """Establish RPC connection using credentials."""
    credentials = load_rpc_credentials('RPC.conf')
    rpc_user = credentials.get("rpc_user", "default_user")
    rpc_password = credentials.get("rpc_password", "default_password")
    rpc_port = credentials.get("rpc_port", "9332")
    rpc_ip = credentials.get("rpc_ip", "localhost")
    return AuthServiceProxy(f"http://{rpc_user}:{rpc_password}@{rpc_ip}:{rpc_port}")

def get_random_tx_data():
    """Get random hex characters from a block's transaction data."""
    rpc_connection = get_rpc_connection()
    block_count = rpc_connection.getblockcount()
    random_block_number = random.randint(max(0, block_count - 1000), block_count)
    block_hash = rpc_connection.getblockhash(random_block_number)
    block = rpc_connection.getblock(block_hash)
    
    tx_data = ""
    if block["tx"]:
        tx_data = ''.join(block["tx"])
    
    return tx_data

def load_icon_mappings(filename):
    """Load slot icon mappings from a configuration file."""
    mapping = {}
    with open(filename, 'r') as file:
        for line in file:
            parts = line.strip().split('=')
            if len(parts) == 2:
                mapping[parts[0]] = parts[1]
    return mapping

def generate_reel_result(mapping, hex_segment):
    """Generate reel result for a specific hex segment."""
    return mapping.get(hex_segment, "default_icon.png")

def spin_reels():
    """Main function to spin reels and generate slot results."""
    reel_results = []
    tx_data = get_random_tx_data()

    if len(tx_data) < 6:
        return ["error"] * 3

    hex_segments = [tx_data[i:i+2] for i in random.sample(range(len(tx_data) - 2), 3)]

    for i in range(1, 4):
        icon_mappings = load_icon_mappings(f"reel{i}_icon_mapping.conf")
        reel_result = generate_reel_result(icon_mappings, hex_segments[i-1])
        reel_results.append(reel_result)

    return reel_results

def generate_html_file(index, tab_index):
    """Generate an HTML file with a unique title and filename."""
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Pull Tab test #{index}</title>
    <script src="/content/2fd9bda05feb18801319b80f8991be03f581a478bf1bcce130183e12c3f7d43ai0"></script>
    <script src="/content/f14f2682a199118d1e541f143367155f551cbc1d0836ce2e7f0a0e473cd35769i0"></script>
</head>
<body tabindex="{tab_index}">
</body>
</html>
"""
    filename = f"./htmls/pulltab_tabindex_{tab_index}#{index}.html"
    with open(filename, 'w') as file:
        file.write(html_content)
    print(f"Generated HTML file: {filename}")

def get_next_index(directory):
    """Get the next index number for the HTML file."""
    if not os.path.exists(directory):
        os.makedirs(directory)
        
    max_index = 0
    for filename in os.listdir(directory):
        if filename.startswith("pulltab_tabindex_") and filename.endswith(".html"):
            try:
                index_part = filename.split("#")[1].replace(".html", "")
                index = int(index_part)
                if index > max_index:
                    max_index = index
            except ValueError:
                continue
    return max_index + 1

def generate_batch_of_html_files(batch_size=100):
    next_index = get_next_index("./htmls")
    
    for _ in range(batch_size):
        results1 = spin_reels()
        results2 = spin_reels()
        results3 = spin_reels()

        # Generate tab_index from results
        tab_index = ''.join([str(int(result[-1])) for result in results1])
        tab_index += ''.join([str(int(result[-1])) for result in results2])
        tab_index += ''.join([str(int(result[-1])) for result in results3])

        # Generate the HTML file
        generate_html_file(next_index, tab_index)

        # Increment the index for the next file
        next_index += 1

if __name__ == "__main__":
    generate_batch_of_html_files()
