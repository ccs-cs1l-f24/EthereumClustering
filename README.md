# Ethereum Address Clustering

## Datasets
1. `centralized_exchanges_data.csv`: originally sourced from [etherclust](https://github.com/etherclust/etherclust/blob/master/data/exchanges.csv) and expanded based on data from Etherscan, contains addresses from large exchanges
2. 

## Functions
`print('start <min-block> <max-block> <exchange-file (optional)> <amount-difference-max (optional)> <block-difference-max (optional)>`
Compiles transaction data from `<min-block>` to `<max-block>` and runs clustering heuristic
`csv <transaction-file> <miner-file>`
Runs clustering heuristic on `<transaction-file>`
`tx <min-block> <max-block>`
Compiles transaction data from `<min-block>` to `<max-block>`