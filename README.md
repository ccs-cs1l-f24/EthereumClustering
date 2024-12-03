# Ethereum Address Clustering
This program implements the deposit address reuse heuristic described by Friedhelm Victor in his paper _Address Clustering Heuristics for Ethereum_. Data is retrieved using the [Etherscan API](https://docs.etherscan.io/etherscan-v2). This is then organized and analyzed to identify addresses that can be grouped into user entities.

## Datasets
1. `centralized_exchanges_data.csv`: originally sourced from [etherclust](https://github.com/etherclust/etherclust/blob/master/data/exchanges.csv) and expanded based on data from Etherscan, contains addresses associated with large exchanges.
2. `dex_data.csv`: contains addresses associated with decentralized exchanges. Sourced from Etherscan.

## Functionality
`start <min-block> <max-block> <exchange-file (optional)> <amount-difference-max (optional)> <block-difference-max (optional)>`
- **Description:** Compiles transaction data from `<min-block>` to `<max-block>` and runs clustering heuristic
- **Parameters:**
    - `<min-block>`: (int) block to start data collection
    - `<max-block>`: (int) block to end data collection (not inclusive)
    - `<exchange-file (optional)>`: (str) dataset of exchange addresses (default is `centralized_exchanges_data.csv`), must be `csv` formatted like default
    - `<amount-difference-max (optional)>`: (float) maximum amount difference parameter (default is 0.01)
    - `<block-difference-max (optional)>`: (int) maximum distance between blocks parameter (default is 3200)

`csv <transaction-file> <miner-file>`
- **Description:** Runs clustering heuristic on provided transaction data
- **Parameters:**
    - `<transaction-file>`: (str) `csv` file formatted like output of `start`
    - `<miner-file>`: (str) `csv` file containing miner addresses

`tx <min-block> <max-block>`
- **Description:** Compiles transaction data from `<min-block>` to `<max-block>`
- **Parameters:**
    - `<min-block>`: (int) block to start data collection
    - `<max-block>`: (int) block to end data collection (not inclusive)
