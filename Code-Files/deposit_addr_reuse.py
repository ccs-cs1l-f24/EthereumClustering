import csv
import requests as req
import pandas as pd

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

    
def generate_transaction_data(api_key, min_block, max_block):
    transactions = []
    miners = []

    for block_tag in range(min_block, max_block):
        req_tx = req.get("https://api.etherscan.io/api?" +
                "module=proxy" + 
                "&action=eth_getBlockByNumber" +
                "&tag=" + hex(block_tag) +
                "&boolean=true" + 
                "&apikey=" + api_key)
        read_tx = req_tx.json()

        miners.append(read_tx["result"]["miner"])
        for transaction in read_tx['result']['transactions']:
            receiver = transaction['to']
            sender = transaction['from']
            amount = transaction['value']
            type_tx = transaction['type']
            temp_row = [block_tag, sender, receiver, amount, type_tx]
            transactions.append(temp_row)
        
    
    with open(str(min_block) + '_to_' + str(max_block) + '_' + "transactions.csv", 'w') as out_file:
        write = csv.writer(out_file)
        write.writerow(['Block Number', "Sender", "Receiver", "Value", "Type"])
        write.writerows(transactions)
    
    with open(str(min_block) + '_to_' + str(max_block) + '_' + "miners.csv", 'w') as out_file:
        write = csv.writer(out_file)
        write.writerow(miners)

    return str(min_block) + '_to_' + str(max_block) + '_' + "transactions.csv", str(min_block) + '_to_' + str(max_block) + '_' + "miners.csv"


def generate_triple_paths(api_key, transactions_file, exchange_file, miner_file):
    addr_exchanges = pd.read_csv(exchange_file)[' address'].tolist()
    addr_miners = pd.read_csv(miner_file).values.tolist()

    tx_df = pd.read_csv(transactions_file)

    possible_deposits = tx_df.index[~tx_df['Sender'].isin(addr_exchanges) & tx_df['Receiver'].isin(addr_exchanges)].tolist()
    possible_deposit_tx = tx_df.iloc[possible_deposits]

    # possible starting points are not exchanges or miners and send to a deposit
    starting_points = tx_df.index[~tx_df['Sender'].isin(addr_exchanges) & ~tx_df['Sender'].isin(addr_miners) & tx_df['Receiver'].isin(tx_df.iloc[possible_deposits]['Sender'])]
    # use the indices to generate a list of the actual transaction objects 
    starting_transactions = tx_df.iloc[starting_points]

    edge_set = []

    # loop through the possible starting addresses to determine which go to possible deposit addresses and use those transactions to construct an edge
    for index, start_tx in starting_transactions.iterrows():
        to_deposit_index = possible_deposit_tx[start_tx['Receiver'] == possible_deposit_tx['Sender']].index.tolist()
        for i in to_deposit_index:
            tempObj = TripleEdge(start_tx, possible_deposit_tx.loc[i])
            edge_set.append(tempObj)

    return edge_set

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
    
    

def dar_heuristic_alg(edges, a_max=1, t_max=10000):
    exchange_entities = {}
    user_entities = {}

    for edge in edges:
        if edge.type_1 = edge.type_2 and edge.value_1 - edge.value_2 <= a_max and edge.block_2 - edge.block_1 <= t_max:
            exchange_entities.setdefault(edge.deposit, []).append(edge.exchange)
            exchange_entities.setdefault(edge.exchange, []).append(edge.deposit)
            user_entities.setdefault(edge.sender, []).append(edge.deposit)
            user_entities.setdefault(edge.deposit, []).append(edge.sender)
    
    num_exchange, exchange_map = wcc(exchange_entities)
    num_user, user_map = wcc(exchange_entities)

    return num_exchange, exchange_map, num_user, user_map

# trans, miner = generate_transaction_data(API_KEY, 21109541, 21109600) # 21109565)
trans="trans_test.csv"
miner = "miner_test.csv"
edges = generate_triple_paths(API_KEY, trans, "data-collection/centralized_exchanges_data.csv", miner)