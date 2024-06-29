import json
import binascii
import re
from decimal import Decimal
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException

# Configuration
NODE_RPC_URL = "http://192.168.68.105:22555"
NODE_RPC_USER = "your_rpc_user"
NODE_RPC_PASS = "your_rpc_password"

# Paths to JSON files
returned_que_json_path = './PullTab/jsons/returnedQue.json'
returned_checked_json_path = './PullTab/jsons/returnedChecked.json'

# Function to get transaction details from Dogecoin node
def get_transaction_details(txid, rpc_user, rpc_pass, rpc_url):
    try:
        # Construct RPC URL with credentials
        rpc_url = f"http://{rpc_user}:{rpc_pass}@{rpc_url.split('://')[1]}"

        # Connect to Dogecoin node via RPC
        rpc_connection = AuthServiceProxy(rpc_url)

        # Retrieve transaction details
        transaction = rpc_connection.getrawtransaction(txid, 1)

        return transaction

    except JSONRPCException as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Unexpected error: {e}"

# Function to process the data string
def process_data_string(data_string):
    target_sequence = "6582895"
    parts = data_string.split()
    
    # Finding the target sequence in the data string
    start_index = data_string.find(target_sequence)
    if start_index == -1:
        raise ValueError(f"Sequence '{target_sequence}' not found in the data")

    # Extracting data from after the sequence
    start_index_data = data_string[start_index + len(target_sequence):].strip()

    # Splitting the data by spaces
    index_parts = start_index_data.split()

    # Extracting the number of chunks
    num_chunks = int(index_parts[0])

    # Extracting the first chunk of data
    first_chunk_hex = index_parts[1]
    MIME_type = bytes.fromhex(first_chunk_hex).decode('utf-8', errors='replace').split(';')[0].strip()

    return num_chunks, parts, MIME_type

# Function to assemble data string from parts
def assemble_data_string(parts, num_chunks):
    data_string = ''
    current_chunk = num_chunks - 1

    while current_chunk >= 0:
        # Search for the current chunk number in parts in each iteration
        for i in range(len(parts)):
            if parts[i] == str(current_chunk):
                # Append the next part to the data string
                if i + 1 < len(parts):
                    data_string += parts[i + 1]
                break

        # Decrease the chunk number for the next iteration
        current_chunk -= 1

    return data_string

# Function to calculate win value based on tabindex
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

# Function to update returnedChecked.json
def update_returned_checked(new_entry):
    try:
        with open(returned_checked_json_path, 'r') as file:
            checked_data = json.load(file)
            if not isinstance(checked_data, list):
                checked_data = []
    except FileNotFoundError:
        checked_data = []

    # Append new entry
    checked_data.append(new_entry)

    # Write updated data back to file
    with open(returned_checked_json_path, 'w') as file:
        json.dump(checked_data, file, indent=4)

    # Print the new entry
    print(f"New entry added to returnedChecked.json: {json.dumps(new_entry, indent=4)}")

# Function to check if a TXID is already in returnedChecked.json
def is_txid_checked(txid):
    try:
        with open(returned_checked_json_path, 'r') as file:
            checked_data = json.load(file)
            for entry in checked_data:
                if entry['utxo'] == txid:
                    return True
    except FileNotFoundError:
        return False
    return False

# Main function to extract ord data
def extract_ord_data():
    with open(returned_que_json_path, 'r') as file:
        data = json.load(file)

    if "returnedQue" not in data or not isinstance(data["returnedQue"], list):
        raise KeyError("The JSON structure is not as expected. Ensure it is a list of objects with an 'utxo' key.")

    for item in data["returnedQue"]:
        if "utxo" not in item:
            continue

        first_txid = item["utxo"]

        if is_txid_checked(first_txid):
            continue

        scriptSig_list = []  # Initialize the list to store 'scriptSig' data
        TXID = first_txid
        target_value = Decimal('0.00100000')
        next_txid = None  # Initialize next_txid
        ord_minter_address = None  # Initialize ord_minter_address

        traced_utxos = []  # List to store all traced UTXOs

        while True:
            transaction = get_transaction_details(TXID, NODE_RPC_USER, NODE_RPC_PASS, NODE_RPC_URL)
            if isinstance(transaction, str) and transaction.startswith("Error"):
                break
            
            traced_utxos.append(TXID)

            found_scriptSig = False

            for vin in transaction['vin']:
                if 'scriptSig' in vin:
                    scriptSig_asm = vin['scriptSig']['asm']
                    scriptSig_list.append(scriptSig_asm)

                    # Check if '6582895' is in the scriptSig_asm
                    if "6582895" in scriptSig_asm:
                        found_scriptSig = True
                        break

            if found_scriptSig:
                break

            # Extract input TXID from the transaction details
            found_input_txid = False
            for vin in transaction['vin']:
                if 'txid' in vin:
                    input_txid = vin['txid']
                    input_vout = vin['vout']

                    input_transaction = get_transaction_details(input_txid, NODE_RPC_USER, NODE_RPC_PASS, NODE_RPC_URL)
                    if isinstance(input_transaction, str) and input_transaction.startswith("Error"):
                        continue

                    for vout in input_transaction['vout']:
                        if vout['n'] == input_vout and Decimal(vout['value']) == target_value:
                            next_txid = input_txid
                            ord_minter_address = vout['scriptPubKey']['addresses'][0]
                            found_input_txid = True
                            break

                    if found_input_txid:
                        break

            if not found_input_txid:
                break

            # Update TXID to the next input TXID and repeat
            TXID = next_txid

        # Once the ord data is found, trace back one more input to find the ord sender address
        ord_sender_address = None
        if next_txid:
            while True:
                transaction = get_transaction_details(next_txid, NODE_RPC_USER, NODE_RPC_PASS, NODE_RPC_URL)
                if isinstance(transaction, str) and transaction.startswith("Error"):
                    break

                found_input = False
                for vin in transaction['vin']:
                    if 'txid' in vin:
                        input_txid = vin['txid']
                        input_vout = vin['vout']

                        input_transaction = get_transaction_details(input_txid, NODE_RPC_USER, NODE_RPC_PASS, NODE_RPC_URL)
                        if isinstance(input_transaction, str) and input_transaction.startswith("Error"):
                            continue

                        for vout in input_transaction['vout']:
                            if vout['n'] == input_vout and Decimal(vout['value']) == target_value:
                                ord_sender_address = vout['scriptPubKey']['addresses'][0]
                                next_txid = input_txid
                                found_input = True
                                break

                        if found_input:
                            break

                if not found_input:
                    break

        # Process the collected scriptSig data
        data_string = ' '.join(scriptSig_list)
        num_chunks, parts, MIME_type = process_data_string(data_string)

        # Assemble data string from parts
        data_string = assemble_data_string(parts, num_chunks)

        # Display data contents of the inscription in the terminal
        if MIME_type == "text/html":
            html_content = binascii.unhexlify(data_string).decode('utf-8', errors='replace')
        else:
            html_content = data_string

        # Extract title and tabindex from HTML content
        title_match = re.search(r'<title>(.*?)</title>', html_content)
        title = title_match.group(1) if title_match else "Unknown Title"
        tabindex_match = re.search(r'tabindex="(\d+)"', html_content)
        tabindex = tabindex_match.group(1) if tabindex_match else "Unknown TabIndex"
        win_value = calculate_win_value(tabindex)

        # Prepare new entry for returnedChecked.json
        new_entry = {
            "utxo": first_txid,
            "previous_address": item["previous_address"],
            "ord_sender_address": ord_sender_address,
            "title": title,
            "tabindex": tabindex,
            "win_value": win_value
        }

        # Update returnedChecked.json with new entry
        update_returned_checked(new_entry)


if __name__ == "__main__":
    extract_ord_data()
