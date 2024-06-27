import json
import time
import itertools
import re
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
import mimetypes
from bs4 import BeautifulSoup

# RPC connection parameters
NODE_RPC_URL = 'http://192.168.68.105:22555'
NODE_RPC_USER = 'your_rpc_user'
NODE_RPC_PASS = 'your_rpc_password'

# Sender address for coin control
SENDER_ADDRESS = 'DMkcx4yQaAfiRea2Gk6qCq8LeZwNQLZcgk'

# Read the returnedQue.json file to get the entries
def read_returnedQue():
    with open('./PullTab/jsons/returnedQue.json', 'r') as file:
        data = json.load(file)
    return data["returnedQue"]

# Read the returnedChecked.json file to get the checked entries
def read_returnedChecked():
    try:
        with open('./PullTab/jsons/returnedChecked.json', 'r') as file:
            data = json.load(file)
        return data["checkedEntries"]
    except FileNotFoundError:
        return []

def get_transaction_details(txid, rpc_url, rpc_user, rpc_pass):
    try:
        rpc_url = f"http://{rpc_user}:{rpc_pass}@{rpc_url.split('://')[1]}"
        rpc_connection = AuthServiceProxy(rpc_url)
        transaction = rpc_connection.getrawtransaction(txid, 1)
        return transaction
    except JSONRPCException as e:
        return f"JSONRPCException: {e}"
    except Exception as e:
        return f"Unexpected error: {e}"

def get_balance(address):
    try:
        rpc_connection = AuthServiceProxy(f"http://{NODE_RPC_USER}:{NODE_RPC_PASS}@{NODE_RPC_URL.split('://')[1]}")
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
        rpc_connection = AuthServiceProxy(f"http://{NODE_RPC_USER}:{NODE_RPC_PASS}@{NODE_RPC_URL.split('://')[1]}")
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
        transaction_details = get_transaction_details(TXID, NODE_RPC_URL, NODE_RPC_USER, NODE_RPC_PASS)
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
            prev_tx_details = get_transaction_details(prev_txid, NODE_RPC_URL, NODE_RPC_USER, NODE_RPC_PASS)
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
    with open('./PullTab/jsons/returnedChecked.json', 'w') as file:
        json.dump({"checkedEntries": checked_data}, file, indent=4)

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

def spinner(seconds):
    spinner = itertools.cycle(['|', '/', '-', '\\'])
    end_time = time.time() + seconds
    while time.time() < end_time:
        print(next(spinner), end='\r', flush=True)
        time.sleep(0.1)
    print(' ', end='\r', flush=True)  # Clear the spinner line

if __name__ == "__main__":
    while True:
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

                if sender_address == "A9VSnfMtG4SLgofaX59ti1hYcJ1hrsHZVX" and win_value > 0:
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
