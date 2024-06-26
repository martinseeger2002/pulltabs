import os
import json
import time
import sys
from decimal import Decimal
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
from datetime import datetime

LOG_FILE_PATH = './transactions.log'
TAB_QUE_FILE_PATH = './PullTab/jsons/tabQue.json'
RETURNED_QUE_FILE_PATH = './PullTab/jsons/returnedQue.json'

# Hard-coded RPC credentials
RPC_USER = "your_rpc_user"
RPC_PASSWORD = "your_rpc_password"
RPC_IP = "192.168.68.105"
RPC_PORT = "22555"

def get_rpc_connection():
    """
    Establish an RPC connection using hard-coded credentials.
    """
    return AuthServiceProxy(f"http://{RPC_USER}:{RPC_PASSWORD}@{RPC_IP}:{RPC_PORT}")

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
    """
    Retrieve the address from the previous transaction's outputs.
    """
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

        # Fetch all UTXOs with at least 1 confirmation
        utxos = rpc_connection.listunspent(1, 9999999, [address])

        # Add time and previous output address information for confirmed transactions
        for utxo in utxos:
            tx_details = rpc_connection.gettransaction(utxo['txid'])
            utxo['time'] = tx_details['blocktime'] if 'blocktime' in tx_details else 'N/A'

            # Get the address from the previous transaction's outputs
            prev_address = get_previous_output_address(rpc_connection, utxo['txid'], utxo['vout'])
            utxo['prev_address'] = prev_address

        # Sort UTXOs by timestamp (ascending order)
        utxos.sort(key=lambda x: x.get('time', float('inf')))

        # Read the existing log file
        logged_txids = read_log_file(LOG_FILE_PATH)
        tab_que = read_json_file(TAB_QUE_FILE_PATH)
        returned_que = read_json_file(RETURNED_QUE_FILE_PATH) if os.path.exists(RETURNED_QUE_FILE_PATH) else {"returnedQue": []}

        new_entries = []

        if utxos:
            for utxo in utxos:
                txid = utxo['txid']
                if txid in logged_txids:
                    continue  # Skip if the txid is already in the log

                confirmations = utxo.get('confirmations', 0)
                amount = Decimal(str(utxo['amount']))
                timestamp = utxo.get('time', 'N/A')
                prev_address = utxo['prev_address']
                readable_time = datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S') if timestamp != 'N/A' else 'N/A'

                # Write the new log entry
                write_log_file(LOG_FILE_PATH, readable_time, amount, prev_address, txid)
                new_entries.append(f"{readable_time} - Received {amount} DOGE from {prev_address} in transaction {txid}")
                
                # Add entries to tabQue for every 10 Dogecoin
                if amount >= 10:
                    num_entries = int(amount // 10)
                    for _ in range(num_entries):
                        tab_que["tabQue"].append({"dogecoin_address": prev_address})
                
                # Add entry to returnedQue if the amount is exactly 0.00100000 Dogecoin
                if amount == Decimal("0.001"):
                    returned_que["returnedQue"].append({"utxo": txid, "previous_address": prev_address})
                    print(f"Added to returnedQue: utxo: {txid}, previous_address: {prev_address}")  # Debug information

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

def spinner():
    while True:
        for cursor in '|/-\\':
            yield cursor

if __name__ == "__main__":
    # Specify the address
    address = "DDwPZVz1TRn9gAcXoFP2XuryvW72kyDZqq"
    
    spin = spinner()
    
    while True:
        # Clear the console line
        sys.stdout.write('\r')
        sys.stdout.write(f'Checking transactions... {next(spin)}')
        sys.stdout.flush()
        
        # Call the function to list received UTXOs
        list_received_utxos(address)
        
        # Wait for 10 seconds before running again, update spinner faster
        for _ in range(10):
            sys.stdout.write('\r')
            sys.stdout.write(f'Checking transactions... {next(spin)}')
            sys.stdout.flush()
            time.sleep(1)
