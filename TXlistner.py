import os
import requests
import json
import time
from datetime import datetime

# Configuration
api_key = "84a74543a2ac4ac1993bd77e38acb312"
wallet_address = "DDwPZVz1TRn9gAcXoFP2XuryvW72kyDZqq"
base_api_url = f"https://api.blockcypher.com/v1/doge/main/addrs/{wallet_address}/full?token={api_key}"
check_interval = 30  # Check interval in seconds
max_additional_calls = 3  # Maximum number of additional API calls

# File paths
transaction_log_path = os.path.join(os.getcwd(), "transactions.log")
tab_que_path = os.path.join(os.getcwd(), "./PullTab/jsons/tabQue.json")

def get_transactions(api_url):
    print("Fetching transactions from API...")
    transactions = []
    api_calls = 0
    while api_url and api_calls < max_additional_calls:
        response = requests.get(api_url)
        api_calls += 1
        if response.status_code == 200:
            response_json = response.json()
            transactions.extend(response_json.get('txs', []))
            print(f"Fetched {len(response_json.get('txs', []))} transactions.")
            if response_json.get('hasMore') and api_calls < max_additional_calls:
                api_url = f"{base_api_url}&before={transactions[-1]['block_height']}"
                print("More transactions available, fetching next batch...")
            else:
                api_url = None
        else:
            print(f"Failed to fetch transactions from API. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return [], api_calls
    print("All transactions fetched successfully.")
    return transactions, api_calls

def parse_log():
    print("Parsing existing transaction log...")
    try:
        with open(transaction_log_path, "r") as f:
            lines = f.readlines()
        tx_hashes = [line.split()[-1] for line in lines if "in transaction" in line]
        print(f"Found {len(tx_hashes)} existing transaction hashes.")
        return tx_hashes
    except FileNotFoundError:
        print("Transaction log not found. Creating a new one.")
        return []

def update_log(new_transactions):
    print(f"Updating transaction log with {len(new_transactions)} new transactions...")
    with open(transaction_log_path, "a") as f:
        for tx in new_transactions:
            timestamp = datetime.strptime(tx['confirmed'], "%Y-%m-%dT%H:%M:%SZ") if 'confirmed' in tx else datetime.now()
            log_entry = f"{timestamp.strftime('%Y-%m-%d %H:%M:%S')} - Received {tx['value'] / 1e8} DOGE from {tx['sender']} in transaction {tx['tx_hash']}\n"
            f.write(log_entry)
    print("Transaction log updated successfully.")

def update_tab_que(new_transactions):
    print("Updating tabQue.json with new transactions...")
    try:
        with open(tab_que_path, "r") as f:
            tab_que = json.load(f)
    except FileNotFoundError:
        print("tabQue.json not found. Creating a new one.")
        tab_que = {"tabQue": []}
    
    for tx in new_transactions:
        count = tx["value"] // 1_000_000_000  # 10 DOGE in satoshis
        for _ in range(count):
            tab_que["tabQue"].append({"dogecoin_address": tx["sender"]})
    
    with open(tab_que_path, "w") as f:
        json.dump(tab_que, f, indent=4)
    print("tabQue.json updated successfully.")

def main():
    processed_hashes = set()
    
    while True:
        print("Starting new transaction check cycle...")
        existing_tx_hashes = parse_log()
        processed_hashes.update(existing_tx_hashes)
        transactions, api_calls = get_transactions(base_api_url)
        
        new_transactions = []
        for tx in transactions:
            tx_hash = tx["hash"]
            if tx_hash not in processed_hashes:
                sender_address = tx["addresses"][0] if "addresses" in tx and tx["addresses"] else "Unknown"
                value = sum(output["value"] for output in tx["outputs"] if wallet_address in output["addresses"])
                new_transactions.append({
                    "tx_hash": tx_hash,
                    "value": value,
                    "sender": sender_address,
                    "confirmed": tx.get("confirmed", datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"))
                })
                processed_hashes.add(tx_hash)
        
        new_transactions.sort(key=lambda x: x['confirmed'])
        
        if new_transactions:
            update_log(new_transactions)
            update_tab_que(new_transactions)
        
        print(f"Scanned {len(transactions)} transactions in {api_calls} API calls. Found {len(new_transactions)} new transactions.")
        print(f"Waiting for {check_interval} seconds before next check...\n")
        
        time.sleep(check_interval)

if __name__ == "__main__":
    main()
