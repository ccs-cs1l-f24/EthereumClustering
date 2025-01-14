import csv
import requests as req
import pandas as pd
import asyncio
import aiohttp
import matplotlib.pyplot as plt
from collections import Counter
import time
import sys
from config import api_key

API_KEY = api_key

# this is an edge of the graph
class Transaction:
    def __init__(self, block, sender, receiver, value, type):
        self.block = block
        self.sender = sender
        self.receiver = receiver
        self.value = value
        self.type = type

# parts of the graph we are interested in
class TripleEdge:
    def __init__(self, tx1, tx2):
        self.sender = tx1['Sender']
        self.deposit = tx1['Receiver']
        self.exchange = tx2['Receiver']
        self.value_1 = int(tx1['Value'], 16)
        self.value_2 = int(tx2['Value'], 16)
        self.type_1 = tx1['Type']
        self.type_2 = tx2['Type']
        self.block_1 = int(tx1['Block Number'])
        self.block_2 = int(tx2['Block Number'])

    def __str__(self):
        return self.sender + ' -> ' + self.deposit + ' -> ' + self.exchange

    def __repr__(self):
        return 'Starting Address:\t' + self.sender + '\nDeposit Address:\t' + self.deposit + '\nExchange Address:\t' + self.exchange


async def process_api_request(session, block_num, api_key, semaphore):
    async with semaphore:
        url = ("https://api.etherscan.io/api?" +
                "module=proxy" + 
                "&action=eth_getBlockByNumber" +
                "&tag=" + hex(block_num) +
                "&boolean=true" + 
                "&apikey=" + api_key)
        async with session.get(url) as response:
            return await response.json()

async def run_concurrent_requests(api_key, min_block, max_block):
    async with aiohttp.ClientSession() as session:
        semaphore = asyncio.Semaphore(5)
        tasks = []

        for block_tag in range(min_block, max_block):
            task = asyncio.create_task(process_api_request(session, block_tag, api_key, semaphore))
            tasks.append(task)
            await asyncio.sleep(1)

        return await asyncio.gather(*tasks, return_exceptions=True)

def generate_transaction_data(min_block, max_block, api_key=API_KEY):
    tasks = asyncio.run(run_concurrent_requests(api_key, min_block, max_block))

    transactions = []
    miners = []

    for block_result, index in zip(tasks, range(min_block, max_block)):
        if isinstance(block_result, Exception):
            print("Error")
            print(block_result)
            continue
        
        try:
            miners.append(block_result["result"]["miner"])
        except:
            print("Error")
            print(block_result)

        for transaction in block_result['result']['transactions']:
            receiver = transaction['to']
            sender = transaction['from']
            amount = transaction['value']
            type_tx = transaction['type']
            temp_row = [index, sender, receiver, amount, type_tx]
            transactions.append(temp_row)

    with open(str(min_block) + '_to_' + str(max_block) + '_' + "transactions.csv", 'w') as out_file:
        write = csv.writer(out_file)
        write.writerow(['Block Number', "Sender", "Receiver", "Value", "Type"])
        write.writerows(transactions)
    
    with open(str(min_block) + '_to_' + str(max_block) + '_' + "miners.csv", 'w') as out_file:
        write = csv.writer(out_file)
        write.writerow(['miners'])
        write.writerow(miners)

    return str(min_block) + '_to_' + str(max_block) + '_' + "transactions.csv", str(min_block) + '_to_' + str(max_block) + '_' + "miners.csv"


def generate_triple_paths(api_key, transactions_file, exchange_file, miner_file):
    # import and filter data
    addr_exchanges = pd.read_csv(exchange_file)[' address'].str.lower()
    addr_miners = pd.read_csv(miner_file)
    tx_df = pd.read_csv(transactions_file)

    # identify possible deposits
    tx_df['Sender'] = tx_df['Sender'].str.lower()
    tx_df['Receiver'] = tx_df['Receiver'].str.lower()

    possible_deposit_tx = tx_df[~tx_df['Sender'].isin(addr_exchanges) & tx_df['Receiver'].isin(addr_exchanges)]
    possible_deposits = possible_deposit_tx['Sender']

    # possible starting points are not exchanges or miners and send to a deposit
    starting_transactions = tx_df[~tx_df['Sender'].isin(addr_exchanges) & ~tx_df['Sender'].isin(addr_miners) & tx_df['Receiver'].isin(possible_deposits)]

    edge_set = []

    # loop through the possible starting addresses to determine which go to possible deposit addresses and use those transactions to construct an edge
    for index, start_tx in starting_transactions.iterrows():
        # identify transactions that start at that deposit address
        to_deposit_tx = possible_deposit_tx[possible_deposit_tx['Sender'] == start_tx['Receiver']]
        for index, deposit_tx in to_deposit_tx.iterrows():
            tempObj = TripleEdge(start_tx, deposit_tx)
            edge_set.append(tempObj)

    return edge_set, possible_deposits

# dictionary based dfs
def wcc(G):
    visited = dict.fromkeys(G.keys(), False)
    components = dict.fromkeys(G.keys(), None)
    comp_num = 0

    def explore(node):
        visited[node] = True
        for adj_node in G[node]:
            if not visited[adj_node]:
                components[adj_node] = comp_num
                explore(adj_node)

    for node in G.keys():
        if not visited[node]:
            components[node] = comp_num
            explore(node)
            comp_num += 1
    
    return comp_num, components
    
    
def dar_heuristic_alg(edges, deposit_addr_list, a_max=1, t_max=10000):
    exchange_entities = {}
    user_entities = {}

    for edge in edges:
        if edge.type_1 == edge.type_2 and edge.value_1 - edge.value_2 <= a_max and edge.block_2 - edge.block_1 <= t_max:
            exchange_entities.setdefault(edge.deposit, []).append(edge.exchange)
            exchange_entities.setdefault(edge.exchange, []).append(edge.deposit)
            user_entities.setdefault(edge.sender, []).append(edge.deposit)
            user_entities.setdefault(edge.deposit, []).append(edge.sender)
    
    num_exchange, exchange_map = wcc(exchange_entities)
    num_user, user_map = wcc(user_entities)
    user_map = {key: value for key, value in user_map.items() if key not in deposit_addr_list}

    return num_exchange, exchange_map, num_user, user_map

def generate_bar_chart(user_dict):
    entities = Counter(list(user_dict.values()))

    plt.bar(range(len(list(entities.keys()))), list(entities.values()), tick_label=list(entities.keys()), label="Entities")
    plt.legend()
    plt.show()

def start_complete(block_start, block_end, exchanges="data-collection/centralized_exchanges_data.csv", amount_diff=0.01, block_diff=3200):
    start_time = time.time()
    
    transactions, miners = generate_transaction_data(block_start, block_end)
    print("Data retrieved. Building graph...")

    edges, deposit_addr_list = generate_triple_paths(API_KEY, transactions, exchanges, miners)
    print('Graph generated. Running deposit address reuse heuristic...')

    num_ex, exchange_out, num_users, user_out = dar_heuristic_alg(edges, deposit_addr_list, amount_diff, block_diff)

    print("Exchanges identified: ", num_ex)
    print("Users identified: ", num_users)
    
    fileout = str(block_start) + '_to_' + str(block_end) + '_user_map.csv'
    with open(fileout, mode='w') as file:
        writer = csv.writer(file)
        writer.writerow(user_out.keys())
        writer.writerows(zip(*user_out.values()))

    print("User map saved to", fileout)
    if num_users > 0:
        generate_bar_chart(user_out)
    end_time = time.time()

    print("Runtime:", end_time - start_time)

def start_from_csv(transactions, miners):
    start_time = time.time()

    exchanges = input("Exchange file (leave empty if default): ") or "data-collection/centralized_exchanges_data.csv"
    amount_diff = float(input('Amount difference maximum (leave empty if default): ') or 0.01)
    block_diff = int(input('Block difference maximum (leave empty if default): ') or 3200)

    edges, deposit_addr_list = generate_triple_paths(API_KEY, transactions, exchanges, miners)
    print('Graph generated. Running deposit address reuse heuristic...')

    num_ex, exchange_out, num_users, user_out = dar_heuristic_alg(edges, deposit_addr_list, amount_diff, block_diff)

    print("Exchanges identified: ", num_ex)
    print("Users identified: ", num_users)
    
    fileout = transactions.split('_transactions.csv')[0] + '_user_map.csv'

    with open(fileout, mode='w') as file:
        writer = csv.DictWriter(file, user_out.keys())
        writer.writeheader()
        writer.writerow(user_out)

    print("User map saved to", fileout)
    if num_users > 0:
        generate_bar_chart(user_out)
    end_time = time.time()

    print("Runtime:", end_time - start_time)

# start_from_csv('5000000_to_5001000_transactions.csv', '5000000_to_5001000_miners.csv')


if sys.argv[1] == '-h':
    print('===== Deposit Address Reuse Clustering =====')
    print('start <min-block> <max-block> <exchange-file (optional)> <amount-difference-max (optional)> <block-difference-max (optional)>')
    print('\t Compiles transaction data from <min-block> to <max-block> and runs clustering heuristic')
    print('csv <transaction-file> <miner-file>')
    print('\t Runs clustering heuristic on <transaction-file>')
    print('tx <min-block> <max-block>')
    print('\t Compiles transaction data from <min-block> to <max-block>')
    print('============================================')
elif sys.argv[1] == 'csv' and len(sys.argv) == 2:
    try:
        start_from_csv(int(sys.argv[2]), int(sys.argv[3]))
    except:
        print('Error... try again')
elif sys.argv[1] == 'start':
    try:
        if len(sys.argv) == 6:
            start_complete(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6])
        else:
            start_complete(sys.argv[2], sys.argv[3])
    except:
        print('Error... try again')
elif sys.argv[1] == 'tx':
    try:
        generate_transaction_data(int(sys.argv[2]), int(sys.argv[3]))
    except:
        print('Error... try again')
else:
    print('Error... try again')

#### TESTING #####
# tx_file = 'test_tx.csv'
# ex_file = 'test_ex.csv'
# miner_file = 'miner_test.csv'
# edge_test, deposits_test = generate_triple_paths(API_KEY, tx_file, ex_file, miner_file)
# num_ex, ex, num_u, u = dar_heuristic_alg(edge_test, deposits_test.tolist())
# print("Exchanges found:", num_ex)
# print("Users found:", num_u)

# print(u)
# generate_bar_chart(u)
