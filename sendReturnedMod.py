import json
import os
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException

# File paths
checked_file_path = './PullTab/jsons/returnedChecked.json'
sent_file_path = './PullTab/jsons/returnedSent.json'

# RPC connection settings
rpc_user = 'your_rpc_user'
rpc_password = 'your_rpc_password'
rpc_port = 22555
rpc_url = f'http://{rpc_user}:{rpc_password}@192.168.68.105:{rpc_port}'

# Address to check balance and send from
source_address = 'DMkcx4yQaAfiRea2Gk6qCq8LeZwNQLZcgk'

def load_json(file_path):
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}. Using an empty list instead.")
        return []
    with open(file_path, 'r') as file:
        return json.load(file)

def save_json(file_path, data):
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)

def check_address_balance(rpc_connection, address):
    try:
        unspent_outputs = rpc_connection.listunspent(1, 9999999, [address])
        balance = sum(output['amount'] for output in unspent_outputs)
        print(f"Balance for {address}: {balance} Dogecoin")  # Debug statement
        return balance
    except JSONRPCException as e:
        print(f"An error occurred while checking the balance: {e}")
        return 0

def send_dogecoin(rpc_connection, to_address, amount):
    try:
        txid = rpc_connection.sendtoaddress(to_address, amount)
        return txid
    except JSONRPCException as e:
        print(f"An error occurred while sending Dogecoin: {e}")
        return None

def check_and_add_entries(checked_entries, sent_entries, sender_address, rpc_connection):
    sent_utxos = {entry['utxo'] for entry in sent_entries}
    not_sent_entries = []
    
    for entry in checked_entries:
        if entry['utxo'] not in sent_utxos and entry['ord_sender_address'] == sender_address and entry['win_value'] > 0:
            balance = check_address_balance(rpc_connection, source_address)
            if balance >= entry['win_value']:
                txid = send_dogecoin(rpc_connection, entry['previous_address'], entry['win_value'])
                if txid:
                    not_sent_entries.append(entry)
                    sent_entries.append(entry)
                    print(f"Sent {entry['win_value']} Dogecoin to {entry['previous_address']} with transaction ID: {txid}")
                else:
                    print(f"Failed to send Dogecoin to {entry['previous_address']}")
            else:
                print(f"Insufficient balance: {balance} Dogecoin")
    
    return not_sent_entries, sent_entries

def main():
    sender_address = "A9VSnfMtG4SLgofaX59ti1hYcJ1hrsHZVX"
    
    # Load JSON data
    checked_entries = load_json(checked_file_path)
    sent_entries = load_json(sent_file_path)
    
    # Connect to RPC
    rpc_connection = AuthServiceProxy(rpc_url)

    # Check for unsent entries, send Dogecoin, and add them to the sent list
    not_sent_entries, updated_sent_entries = check_and_add_entries(checked_entries, sent_entries, sender_address, rpc_connection)

    # Save the updated sent list back to the file
    save_json(sent_file_path, updated_sent_entries)

    # Print results
    if not_sent_entries:
        print(f"The following entries have been added to the sent list:\n{json.dumps(not_sent_entries, indent=4)}")


if __name__ == "__main__":
    main()
