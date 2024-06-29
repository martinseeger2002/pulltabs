import subprocess
import time
import json
import re
import os
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException

# Read RPC credentials from environment variables
rpc_url = os.getenv('NODE_RPC_URL', 'http://192.168.68.105:22555')
rpc_user = os.getenv('NODE_RPC_USER', 'your_rpc_user')
rpc_password = os.getenv('NODE_RPC_PASS', 'your_rpc_password')

# Construct the full RPC URL with credentials
full_rpc_url = f"http://{rpc_user}:{rpc_password}@{rpc_url.split('://')[1]}"

rpc_connection = AuthServiceProxy(full_rpc_url)

def read_last_output(json_file_name):
    if os.path.exists(json_file_name):
        try:
            with open(json_file_name, 'r') as file:
                data = json.load(file)
                return len(data)
        except json.JSONDecodeError as e:
            print(f"JSON decode error in {json_file_name}: {e}")
    return 0

def get_last_inscribed_index(json_file_name):
    if os.path.exists(json_file_name):
        try:
            with open(json_file_name, 'r') as file:
                data = json.load(file)
                if data:
                    last_key = list(data.keys())[-1]
                    match = re.search(r'#(\d+)\.html$', last_key)
                    if match:
                        return int(match.group(1))
        except json.JSONDecodeError as e:
            print(f"JSON decode error in {json_file_name}: {e}")
    return -1

def extract_details(file_name):
    try:
        with open(file_name, 'r', encoding='utf-8') as file:
            details = json.load(file).get('tabQue', [])
            return details
    except FileNotFoundError:
        print(f"File {file_name} not found.")
        raise
    except Exception as e:
        print(f"An error occurred while reading {file_name}: {e}")
        return []

def update_json_file(json_path, txid, filename, address):
    json_file_name = os.path.join(json_path, "sentTab.json")
    try:
        data = {}
        if os.path.exists(json_file_name):
            with open(json_file_name, 'r') as file:
                data = json.load(file)
        data[filename] = {"txid": txid, "address": address}
        with open(json_file_name, 'w') as file:
            json.dump(data, file, indent=4)
    except Exception as e:
        print(f"Error updating {json_file_name}: {e}")

def calculate_win_value(tabindex):
    win_table = {
        '111': 9,
        '222': 15,
        '333': 30,
        '444': 75,
        '555': 150,
        '666': 300,
        '777': 600
    }
    matches = re.findall(r'(\d{3})', tabindex)
    win_values = [win_table.get(set_num, 0) for set_num in matches]
    return sum(win_values)

def update_ow_json(json_path, txid, win_value, number):
    json_file_name = os.path.join(json_path, "OW.json")
    try:
        data = []
        if os.path.exists(json_file_name):
            with open(json_file_name, 'r') as file:
                data = json.load(file)
        entry = {
            "id": txid,
            "meta": {
                "name": f"Pull Tab test #{number}",
                "attributes": [
                    {
                        "trait_type": "win",
                        "value": f"{win_value}"
                    }
                ]
            }
        }
        data.append(entry)
        with open(json_file_name, 'w') as file:
            json.dump(data, file, indent=4)
    except Exception as e:
        print(f"Error updating {json_file_name}: {e}")

def build_file_index(html_path):
    file_index = {}
    for filename in os.listdir(html_path):
        if filename.endswith('.html'):
            match = re.search(r'#(\d+)\.html', filename)
            if match:
                number = int(match.group(1))
                file_index[number] = filename
    return file_index

def find_matching_file(file_index, number):
    return file_index.get(number, None)

def process_mint_batch(start, end, html_path, json_path, details_list, file_index):
    last_txid = ""
    for i in range(start, min(end + 1, len(details_list) + start)):
        actual_index = i - start
        if actual_index >= len(details_list):
            break
        details = details_list[actual_index]
        next_filename = find_matching_file(file_index, start + actual_index)
        if not next_filename:
            continue
        image_path = os.path.join(html_path, next_filename)
        mint_command = f"node . mint {details['dogecoin_address']} {image_path}"
        result_mint = subprocess.run(mint_command, shell=True, capture_output=True, text=True, cwd=r'C:\doginals-main')
        txid_search = re.search(r"inscription txid: (\w+)", result_mint.stdout)
        if txid_search:
            last_txid = txid_search.group(1)
            modified_txid = f"{last_txid}i0"
            win_value = calculate_win_value(next_filename)
            number = start + actual_index
            update_json_file(json_path, modified_txid, next_filename, details['dogecoin_address'])
            update_ow_json(json_path, modified_txid, win_value, number)
            print(f"Successful mint, TXID: {modified_txid}")
        if result_mint.stderr:
            print("Error in mint command:")
            print(result_mint.stderr)
    return last_txid

def wait_for_tx_confirmation(txid):
    while True:
        try:
            tx_info = rpc_connection.gettransaction(txid)
            if tx_info and tx_info.get("confirmations", 0) >= 1:
                print(f"Transaction {txid} is confirmed.")
                break
        except JSONRPCException as e:
            print(f"Error fetching transaction {txid}: {e}")
        time.sleep(10)

def run_minting_process_once(html_path, json_path, start_number):
    try:
        if not os.path.exists(os.path.join(json_path, 'sentTab.json')):
            with open(os.path.join(json_path, 'sentTab.json'), 'w') as file:
                json.dump({}, file)
        if not os.path.exists(os.path.join(json_path, 'OW.json')):
            with open(os.path.join(json_path, 'OW.json'), 'w') as file:
                json.dump([], file)
        last_index = get_last_inscribed_index(os.path.join(json_path, 'sentTab.json'))
        details_list = extract_details(os.path.join(json_path, 'tabQue.json'))
        if not details_list:
            return
        if last_index >= 0:
            details_list = details_list[last_index:]
        else:
            last_index = 0
        file_index = build_file_index(html_path)
        batch_size = 12
        num_batches = (len(details_list) + batch_size - 1) // batch_size
        if num_batches == 0:
            return
        for batch_index in range(num_batches):
            start_index = last_index + batch_index * batch_size
            end_index = start_index + batch_size - 1
            last_txid = process_mint_batch(start_index + 1, end_index + 1, html_path, json_path, details_list, file_index)
            if last_txid:
                wait_for_tx_confirmation(last_txid)
    except FileNotFoundError as fnfe:
        print(f"An error occurred: {fnfe}")
    except Exception as e:
        print(f"An error occurred: {e}")

# Initialize main variables and start process
html_path = r'C:\doginals-main\PullTab\htmls'
json_path = r'C:\doginals-main\PullTab\jsons'
start_number = 1

run_minting_process_once(html_path, json_path, start_number)
