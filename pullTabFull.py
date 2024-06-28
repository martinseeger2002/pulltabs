import os
import json
import time
import re
import itertools
from decimal import Decimal
from datetime import datetime
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
import subprocess
from bs4 import BeautifulSoup

# User-specific variables
RPC_USER = "your_rpc_user"
RPC_PASSWORD = "your_rpc_password"
RPC_IP = "192.168.68.105"
RPC_PORT = "22555"
NODE_RPC_URL = f"http://{RPC_USER}:{RPC_PASSWORD}@{RPC_IP}:{RPC_PORT}"
SENDER_ADDRESS = 'DMkcx4yQaAfiRea2Gk6qCq8LeZwNQLZcgk'
ORD_SENDER_ADDRESS = "A9VSnfMtG4SLgofaX59ti1hYcJ1hrsHZVX"

LOG_FILE_PATH = './transactions.log'
TAB_QUE_FILE_PATH = './PullTab/jsons/tabQue.json'
RETURNED_QUE_FILE_PATH = './PullTab/jsons/returnedQue.json'
RETURNED_CHECKED_FILE_PATH = './PullTab/jsons/returnedChecked.json'
HTML_PATH = r'C:\doginals-main\PullTab\htmls'
JSON_PATH = r'C:\doginals-main\PullTab\jsons'
START_NUMBER = 1

win_table = {
    '111': 9,
    '222': 15,
    '333': 30,
    '444': 75,
    '555': 150,
    '666': 300,
    '777': 600
}

def get_rpc_connection():
    return AuthServiceProxy(NODE_RPC_URL)

def read_log_file(filepath):
    existing_txids = set()
    if os.path.exists(filepath):
        with open(filepath, 'r') as file:
            for line in file:
                parts = line.strip().split()
                if len(parts) > 1:
                    txid = parts[-1]
                    existing_txids.add(txid)
    return existing_txids

def write_log_file(filepath, timestamp, amount, prev_address, txid):
    log_entry = f"{timestamp} - Received {amount} DOGE from {prev_address} in transaction {txid}"
    with open(filepath, 'a') as file:
        file.write(f"{log_entry}\n")

def read_json_file(filepath):
    if not os.path.exists(filepath):
        return {"tabQue": []}
    with open(filepath, 'r') as file:
        return json.load(file)

def write_json_file(filepath, data):
    with open(filepath, 'w') as file:
        json.dump(data, file, indent=4)

def get_previous_output_address(rpc_connection, txid, vout_index):
    try:
        raw_tx = rpc_connection.getrawtransaction(txid, True)
        if vout_index < len(raw_tx['vin']):
            prev_txid = raw_tx['vin'][vout_index]['txid']
            prev_vout_index = raw_tx['vin'][vout_index]['vout']
            prev_tx = rpc_connection.getrawtransaction(prev_txid, True)
            prev_vout = prev_tx['vout'][prev_vout_index]
            if 'addresses' in prev_vout['scriptPubKey']:
                return prev_vout['scriptPubKey']['addresses'][0]
    except Exception as e:
        print(f"Error in getting previous output address: {e}")
    return None

def list_received_utxos(address):
    try:
        rpc_connection = get_rpc_connection()
        utxos = rpc_connection.listunspent(1, 9999999, [address])
        for utxo in utxos:
            tx_details = rpc_connection.gettransaction(utxo['txid'])
            utxo['time'] = tx_details['blocktime'] if 'blocktime' in tx_details else 'N/A'
            prev_address = get_previous_output_address(rpc_connection, utxo['txid'], utxo['vout'])
            utxo['prev_address'] = prev_address
        utxos.sort(key=lambda x: x.get('time', float('inf')))
        logged_txids = read_log_file(LOG_FILE_PATH)
        tab_que = read_json_file(TAB_QUE_FILE_PATH)
        returned_que = read_json_file(RETURNED_QUE_FILE_PATH) if os.path.exists(RETURNED_QUE_FILE_PATH) else {"returnedQue": []}
        new_entries = []
        if utxos:
            for utxo in utxos:
                txid = utxo['txid']
                if txid in logged_txids:
                    continue
                confirmations = utxo.get('confirmations', 0)
                amount = Decimal(str(utxo['amount']))
                timestamp = utxo.get('time', 'N/A')
                prev_address = utxo['prev_address']
                readable_time = datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S') if timestamp != 'N/A' else 'N/A'
                write_log_file(LOG_FILE_PATH, readable_time, amount, prev_address, txid)
                new_entries.append(f"{readable_time} - Received {amount} DOGE from {prev_address} in transaction {txid}")
                if amount >= 10:
                    num_entries = int(amount // 10)
                    for _ in range(num_entries):
                        tab_que["tabQue"].append({"dogecoin_address": prev_address})
                if amount == Decimal("0.001"):
                    returned_que["returnedQue"].append({"utxo": txid, "previous_address": prev_address})
                    print(f"Added to returnedQue: utxo: {txid}, previous_address: {prev_address}")
        write_json_file(TAB_QUE_FILE_PATH, tab_que)
        write_json_file(RETURNED_QUE_FILE_PATH, returned_que)
        if new_entries:
            print(f"\nNew UTXOs in address {address}:")
            for entry in new_entries:
                print(f"  - {entry}")
    except JSONRPCException as e:
        print(f"\nAn error occurred: {e}")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")

def spinner(seconds):
    spin = itertools.cycle(['|', '/', '-', '\\'])
    end_time = time.time() + seconds
    while time.time() < end_time:
        print(next(spin), end='\r', flush=True)
        time.sleep(0.1)
    print(' ', end='\r', flush=True)

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
            print(f"Extracted {len(details)} details from {file_name}")
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
        print(f"Updated {json_file_name} with {filename}: {txid}, {address}")
    except Exception as e:
        print(f"Error updating {json_file_name}: {e}")

def calculate_win_value(tabindex):
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
        print(f"Updated {json_file_name} with new entry: {entry}")
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
            print(f"Index {i} exceeds the length of details_list {len(details_list)}")
            break
        details = details_list[actual_index]
        next_filename = find_matching_file(file_index, start + actual_index)
        if not next_filename:
            print(f"File not found for number: {start + actual_index}")
            continue
        image_path = os.path.join(html_path, next_filename)
        print(f"Processing file: {image_path} for address: {details['dogecoin_address']}")
        mint_command = f"node . mint {details['dogecoin_address']} {image_path}"
        result_mint = subprocess.run(mint_command, shell=True, capture_output=True, text=True, cwd=r'C:\doginals-main')
        print("Output from mint command:")
        print(result_mint.stdout)
        if result_mint.stderr:
            print("Error in mint command:")
            print(result_mint.stderr)
        txid_search = re.search(r"inscription txid: (\w+)", result_mint.stdout)
        if txid_search:
            last_txid = txid_search.group(1)
            modified_txid = f"{last_txid}i0"
            print(f"Successful mint, TXID: {modified_txid}")
            win_value = calculate_win_value(next_filename)
            number = start + actual_index
            update_json_file(json_path, modified_txid, next_filename, details['dogecoin_address'])
            update_ow_json(json_path, modified_txid, win_value, number)
        else:
            print("No TXID found in mint command output.")
    return last_txid

def wait_for_tx_confirmation(txid, html_path, json_path, start_number):
    while True:
        try:
            tx_info = rpc_connection.gettransaction(txid)
            if tx_info and tx_info.get("confirmations", 0) >= 1:
                print(f"Transaction {txid} is confirmed.")
                break
        except JSONRPCException as e:
            print(f"Error fetching transaction {txid}: {e}")
        time.sleep(10)
    continuous_minting_process(html_path, json_path, start_number)

def continuous_minting_process(html_path, json_path, start_number):
    try:
        if not os.path.exists(os.path.join(json_path, 'sentTab.json')):
            with open(os.path.join(json_path, 'sentTab.json'), 'w') as file:
                json.dump({}, file)
        if not os.path.exists(os.path.join(json_path, 'OW.json')):
            with open(os.path.join(json_path, 'OW.json'), 'w') as file:
                json.dump([], file)
        last_index = get_last_inscribed_index(os.path.join(json_path, 'sentTab.json'))
        print(f"Starting minting process from last inscribed index: {last_index}")
        details_list = extract_details(os.path.join(json_path, 'tabQue.json'))
        if not details_list:
            print("No details to process.")
            return
        if last_index >= 0:
            details_list = details_list[last_index:]
        else:
            last_index = 0
        file_index = build_file_index(html_path)
        batch_size = 12
        num_batches = (len(details_list) + batch_size - 1) // batch_size
        print(f"Total batches to process: {num_batches}")
        if num_batches == 0:
            raise ValueError("Total batches to process is 0")
        for batch_index in range(num_batches):
            start_index = last_index + batch_index * batch_size
            end_index = start_index + batch_size - 1
            print(f"Processing batch from {start_index + 1} to {end_index + 1}")
            last_txid = process_mint_batch(start_index + 1, end_index + 1, html_path, json_path, details_list, file_index)
            if last_txid:
                print(f"Waiting for confirmation of TXID: {last_txid}")
                wait_for_tx_confirmation(last_txid, html_path, json_path, start_number)
            else:
                print("No valid transactions in this batch to wait for.")
    except FileNotFoundError as fnfe:
        print(f"An error occurred: {fnfe}")
        print("Waiting 100 seconds before retrying...")
        time.sleep(100)
        continuous_minting_process(html_path, json_path, start_number)
    except Exception as e:
        print(f"An error occurred: {e}")
        print("Waiting 100 seconds before retrying...")
        time.sleep(100)
        pending_txs_path = os.path.join(os.getcwd(), 'pending-txs.json')
        if os.path.exists(pending_txs_path):
            try:
                os.remove(pending_txs_path)
                print(f"Deleted {pending_txs_path}")
            except Exception as delete_error:
                print(f"Error deleting {pending_txs_path}: {delete_error}")
        continuous_minting_process(html_path, json_path, start_number)

def read_returnedQue():
    with open(RETURNED_QUE_FILE_PATH, 'r') as file:
        data = json.load(file)
    return data["returnedQue"]

def read_returnedChecked():
    try:
        with open(RETURNED_CHECKED_FILE_PATH, 'r') as file:
            data = json.load(file)
        return data["checkedEntries"]
    except FileNotFoundError:
        return []

def get_transaction_details(txid):
    try:
        rpc_connection = get_rpc_connection()
        transaction = rpc_connection.getrawtransaction(txid, 1)
        return transaction
    except JSONRPCException as e:
        return f"JSONRPCException: {e}"
    except Exception as e:
        return f"Unexpected error: {e}"

def get_balance(address):
    try:
        rpc_connection = get_rpc_connection()
        balance = rpc_connection.getreceivedbyaddress(address)
        return balance
    except JSONRPCException as e:
        print(f"Error getting balance: {e}")
        return 0
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 0

def send_dogecoin(previous_address, amount):
    try:
        rpc_connection = get_rpc_connection()
        txid = rpc_connection.sendtoaddress(previous_address, amount)
        print(f"Transaction sent. TXID: {txid}")
        return True
    except JSONRPCException as e:
        print(f"Error sending transaction: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

def extract_data(txid):
    global TXID
    TXID = txid
    scriptSig_list = []
    sender_address = None

    while True:
        transaction_details = get_transaction_details(TXID)
        if isinstance(transaction_details, str) and 'error' in transaction_details.lower():
            print(transaction_details)
            break
        print(f"Checking for '6582895' in {TXID}")
        scriptSig_asm = transaction_details['vin'][0]['scriptSig']['asm']
        scriptSig_list.append(scriptSig_asm)
        if "6582895" in scriptSig_asm:
            print(f"TXID containing '6582895': {TXID}")
            with open('temp_scriptSig_list.txt', 'w') as file:
                file.write(' '.join(scriptSig_list))
            prev_txid = transaction_details['vin'][0]['txid']
            prev_vout_index = transaction_details['vin'][0]['vout']
            prev_tx_details = get_transaction_details(prev_txid)
            if isinstance(prev_tx_details, str) and 'error' in prev_tx_details.lower():
                print(prev_tx_details)
                break
            sender_address = prev_tx_details['vout'][prev_vout_index]['scriptPubKey']['addresses'][0]
            break
        if not transaction_details['vin']:
            print("No further input TXIDs to follow. Exiting.")
            break
        TXID = transaction_details['vin'][0]['txid']
    return sender_address

def process_file(file_path):
    target_sequence = "6582895"
    with open(file_path, 'r') as file:
        data = file.read()
    parts = data.split()
    start_index = data.find(target_sequence)
    if start_index == -1:
        raise ValueError(f"Sequence '{target_sequence}' not found in the file")
    start_index_data = data[start_index + len(target_sequence):].strip()
    index_parts = start_index_data.split()
    num_chunks = int(index_parts[0])
    first_chunk_hex = index_parts[1]
    MIME_type = bytes.fromhex(first_chunk_hex).decode('utf-8', errors='replace')
    return num_chunks, parts, MIME_type

def assemble_data_string(parts, num_chunks):
    data_string = ''
    current_chunk = num_chunks - 1
    while current_chunk >= 0:
        for i in range(len(parts)):
            if parts[i] == str(current_chunk):
                if i + 1 < len(parts):
                    data_string += parts[i + 1]
                break
        current_chunk -= 1
    return data_string

def extract_html_data(data_hex):
    data_bytes = bytes.fromhex(data_hex)
    html_content = data_bytes.decode('utf-8', errors='replace')
    soup = BeautifulSoup(html_content, 'html.parser')
    title = soup.title.string if soup.title else 'No title found'
    tabindex = soup.body['tabindex'] if soup.body and 'tabindex' in soup.body.attrs else 'No tabindex found'
    return title, tabindex

def save_checked_data(checked_data):
    with open(RETURNED_CHECKED_FILE_PATH, 'w') as file:
        json.dump({"checkedEntries": checked_data}, file, indent=4)

def main():
    while True:
        address = "DDwPZVz1TRn9gAcXoFP2XuryvW72kyDZqq"
        print(f"Checking transactions for {address}...")
        list_received_utxos(address)
        print("Starting minting process...")
        continuous_minting_process(HTML_PATH, JSON_PATH, START_NUMBER)
        print("Processing returned queue...")
        original_entries = read_returnedQue()
        checked_entries = read_returnedChecked()
        checked_txids = {entry["utxo"] for entry in checked_entries}
        for entry in original_entries:
            if entry["utxo"] not in checked_txids:
                txid = entry["utxo"]
                sender_address = extract_data(txid)
                if sender_address:
                    print(f"Sender Address: {sender_address}")
                file_path = 'temp_scriptSig_list.txt'
                num_chunks, file_parts, MIME_type = process_file(file_path)
                data_string = assemble_data_string(file_parts, num_chunks)
                primary_mime_type = MIME_type.split(';')[0].strip()
                if primary_mime_type == 'text/html':
                    title, tabindex = extract_html_data(data_string)
                    print(f"Title: {title}")
                    print(f"Tabindex: {tabindex}")
                    win_value = calculate_win_value(tabindex)
                    print(f"Win Value: {win_value}")
                else:
                    title, tabindex, win_value = 'N/A', 'N/A', 0
                    print(f"Data is not HTML. MIME type: {MIME_type}")
                if sender_address == ORD_SENDER_ADDRESS and win_value > 0:
                    previous_address = entry["previous_address"]
                    balance = get_balance(SENDER_ADDRESS)
                    if balance >= win_value:
                        if send_dogecoin(previous_address, win_value):
                            entry["ord_sender_address"] = sender_address
                            entry["title"] = title
                            entry["tabindex"] = tabindex
                            entry["win_value"] = win_value
                            checked_entries.append(entry)
                    else:
                        print(f"Insufficient balance to send {win_value} DOGE to {previous_address}.")
                else:
                    entry["ord_sender_address"] = sender_address
                    entry["title"] = title
                    entry["tabindex"] = tabindex
                    entry["win_value"] = win_value
                    checked_entries.append(entry)
        save_checked_data(checked_entries)
        spinner(30)

if __name__ == "__main__":
    main()
