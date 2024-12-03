import csv
import requests as req
import pandas as pd
import asyncio
import aiohttp

API_KEY = "BIYUJTNDT1C26ZIEP1YWT2AXUHFXVN5683"

class Transaction:
    def __init__(self, block, sender, receiver, value, type):
        self.block = block
        self.sender = sender
        self.receiver = receiver
        self.value = value
        self.type = type

class TripleEdge:
    def __init__(self, tx1, tx2):
        self.sender = tx1['Sender']
        self.deposit = tx1['Receiver']
        self.exchange = tx2['Receiver']
        self.value_1 = tx1['Value']
        self.value_2 = tx2['Value']
        self.type_1 = tx1['Type']
        self.type_2 = tx2['Type']
        self.block_1 = tx1['Block Number']
        self.block_2 = tx2['Block Number']

    def __str__(self):
        return self.sender + ' -> ' + self.deposit + ' -> ' + self.exchange

    def __repr__(self):
        return 'Starting Address:\t' + self.sender + '\nDeposit Address:\t' + self.deposit + '\nExchange Address:\t' + self.exchange


async def process_api_request(session, block_num, api_key):
    try:
        resp = await session.get("https://api.etherscan.io/api?" +
                "module=proxy" + 
                "&action=eth_getBlockByNumber" +
                "&tag=" + hex(block_num) +
                "&boolean=true" + 
                "&apikey=" + api_key)
        return await resp.json()
    except Exception as e:
        print(f"Error: {str(e)}")
        print("Occured at BLOCK", block_num)

async def run_concurrent_requests(api_key, min_block, max_block):
    async with aiohttp.ClientSession() as session:
        tasks = []

        for block_tag in range(min_block, max_block):
            tasks.append(process_api_request(session, block_tag, api_key))

        return await asyncio.gather(*tasks, return_exceptions=True)

def generate_transaction_data(api_key, min_block, max_block):
    tasks = asyncio.run(run_concurrent_requests(api_key, min_block, max_block))

    transactions = []
    miners = []

    for block_result in tasks:
        if isinstance(block_result, Exception):
            print("Error")
            continue
        
        miners.append(block_result["result"]["miner"])

        for transaction, index in zip(block_result['result']['transactions'], range(min_block, max_block)):
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
    addr_exchanges = pd.read_csv(exchange_file)[' address']
    addr_miners = pd.read_csv(miner_file)
    tx_df = pd.read_csv(transactions_file)

    # identify possible deposits
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

def start():
    block_start = int(input('Start Block: '))
    block_end = int(input('End Block: '))

    exchanges = input("Exchange file (leave empty if default): ") or "data-collection/centralized_exchanges_data.csv"
    amount_diff = float(input('Amount difference maximum: ') or 0.01)
    block_diff = int(input('Block difference maximum: ') or 3200)

    transactions, miners = generate_transaction_data(API_KEY, block_start, block_end)
    print("Data retrieved. Building graph...")``

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

start()

##### TESTING #####
# tx_file = 'test_tx.csv'
# ex_file = 'test_ex.csv'
# miner_file = 'miner_test.csv'
# edge_test, deposits_test = generate_triple_paths(API_KEY, tx_file, ex_file, miner_file)
# num_ex, ex, num_u, u = dar_heuristic_alg(edge_test, deposits_test.tolist())
# print("Exchanges found:", num_ex)
# print("Users found:", num_u)

# print(u)