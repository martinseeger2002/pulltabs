import os
import time
import logging
import json
import requests
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
from http.client import RemoteDisconnected
from datetime import datetime

# Set environment variables
os.environ['NODE_RPC_URL'] = '192.168.68.105:22555'
os.environ['NODE_RPC_USER'] = 'your_rpc_user'
os.environ['NODE_RPC_PASS'] = 'your_rpc_password'

# Retrieve environment variables
rpc_host = os.getenv('NODE_RPC_URL')
rpc_user = os.getenv('NODE_RPC_USER')
rpc_password = os.getenv('NODE_RPC_PASS')

# Construct the RPC URL with credentials
rpc_url = f'http://{rpc_user}:{rpc_password}@{rpc_host}'

# Print to debug the environment variable values
print(f"Connecting to {rpc_url}")

# Dogecoin address to listen to
watch_address = 'DDwPZVz1TRn9gAcXoFP2XuryvW72kyDZqq'

# Setup logging
logging.basicConfig(filename='transactions.log', level=logging.INFO,
                    format='%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

def create_rpc_connection():
    return AuthServiceProxy(rpc_url)

def get_latest_block(rpc_connection):
    try:
        return rpc_connection.getbestblockhash()
    except (JSONRPCException, RemoteDisconnected, OSError) as e:
        print(f"An error occurred while fetching the latest block: {e}")
        return None

def get_block_transactions(rpc_connection, block_hash):
    try:
        block = rpc_connection.getblock(block_hash)
        return block['tx']
    except (JSONRPCException, RemoteDisconnected, OSError) as e:
        print(f"An error occurred while fetching block transactions: {e}")
        return []

def get_transaction_details(rpc_connection, txid):
    try:
        raw_tx = rpc_connection.getrawtransaction(txid)
        decoded_tx = rpc_connection.decoderawtransaction(raw_tx)
        return decoded_tx
    except (JSONRPCException, RemoteDisconnected, OSError) as e:
        print(f"An error occurred while fetching transaction details: {e}")
        return None

def get_previous_output_address(rpc_connection, tx_input):
    try:
        raw_tx = rpc_connection.getrawtransaction(tx_input['txid'])
        decoded_tx = rpc_connection.decoderawtransaction(raw_tx)
        output = decoded_tx['vout'][tx_input['vout']]
        addresses = output['scriptPubKey'].get('addresses', [])
        return addresses[0] if addresses else 'unknown'
    except (JSONRPCException, RemoteDisconnected, OSError) as e:
        print(f"An error occurred while fetching previous output address: {e}")
        return 'unknown'

def initialize_tabque_json(json_file_name):
    if not os.path.exists(json_file_name) or os.path.getsize(json_file_name) == 0:
        with open(json_file_name, 'w') as file:
            json.dump({'tabQue': []}, file)

def update_tabque_json(address, amount):
    json_file_name = r'C:\doginals-main\PullTab\jsons\tabQue.json'
    try:
        initialize_tabque_json(json_file_name)
        with open(json_file_name, 'r') as file:
            data = json.load(file)
        
        entries_to_add = int(amount // 10)
        new_entries = [{'dogecoin_address': address} for _ in range(entries_to_add)]
        
        data['tabQue'].extend(new_entries)
        
        with open(json_file_name, 'w') as file:
            json.dump(data, file, indent=4)
        
        print(f"Added {entries_to_add} entries to {json_file_name} for address: {address}")
    except Exception as e:
        print(f"Error updating {json_file_name}: {e}")

def process_transactions(rpc_connection, transactions, processed_txids):
    for txid in transactions:
        if txid not in processed_txids:
            tx_details = get_transaction_details(rpc_connection, txid)
            if tx_details:
                for output in tx_details['vout']:
                    if 'addresses' in output['scriptPubKey'] and watch_address in output['scriptPubKey']['addresses']:
                        amount = output['value']
                        from_address = get_previous_output_address(rpc_connection, tx_details['vin'][0])
                        log_message = f"Received {amount} DOGE from {from_address} in transaction {txid}"
                        if log_message not in processed_txids:
                            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            full_log_message = f"{timestamp} - {log_message}"
                            print(full_log_message)
                            logging.info(full_log_message)
                            processed_txids.add(log_message)
                        
                        if amount >= 10:
                            update_tabque_json(from_address, amount)

def check_api_and_update_log():
    api_url = f'https://api.blockcypher.com/v1/doge/main/addrs/{watch_address}/full'
    try:
        response = requests.get(api_url)
        if response.status_code == 200:
            transactions = response.json().get('txs', [])
            with open('transactions.log', 'r') as log_file:
                logged_txids = set(line.split()[-1] for line in log_file.readlines() if 'transaction' in line)
            new_transactions = [tx for tx in transactions if tx['hash'] not in logged_txids]
            if new_transactions:
                with open('transactions.log', 'a') as log_file:
                    for tx in new_transactions:
                        amount = sum(output['value'] for output in tx['outputs'] if watch_address in output['addresses'])
                        from_address = tx['inputs'][0]['addresses'][0]
                        # Handle timestamps with and without microseconds
                        try:
                            timestamp = datetime.strptime(tx['received'], '%Y-%m-%dT%H:%M:%S.%fZ').strftime('%Y-%m-%d %H:%M:%S')
                        except ValueError:
                            timestamp = datetime.strptime(tx['received'], '%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m-%d %H:%M:%S')
                        log_message = f"Received {amount / 1e8} DOGE from {from_address} in transaction {tx['hash']}"
                        full_log_message = f"{timestamp} - {log_message}"
                        if tx['hash'] not in logged_txids:
                            print(full_log_message)
                            logging.info(full_log_message)
                            log_file.write(full_log_message + '\n')
                        if amount >= 10 * 1e8:
                            update_tabque_json(from_address, amount / 1e8)
        else:
            print(f"Error checking API: Status code {response.status_code}")
    except requests.RequestException as e:
        print(f"Error checking API: {e}")

def main():
    print(f"Listening for transactions to {watch_address}...")
    processed_txids = set()
    retry_attempts = 0
    max_retries = 5  # Maximum number of retries before exiting
    retry_delay = 10  # Delay in seconds between retries

    while True:
        rpc_connection = create_rpc_connection()

        latest_block_hash = get_latest_block(rpc_connection)
        if latest_block_hash is None:
            retry_attempts += 1
            if retry_attempts > max_retries:
                print("Max retries reached. Exiting.")
                break
            print(f"Reconnecting to the Dogecoin node... (Attempt {retry_attempts}/{max_retries})")
            time.sleep(retry_delay)
            continue
        else:
            retry_attempts = 0  # Reset retry attempts on successful connection

        block_transactions = get_block_transactions(rpc_connection, latest_block_hash)
        process_transactions(rpc_connection, block_transactions, processed_txids)

        check_api_and_update_log()
        time.sleep(21600)  # Check the API and update every 6 hours

if __name__ == "__main__":
    main()
