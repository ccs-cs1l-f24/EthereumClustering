import requests as req

API_KEY = "BIYUJTNDT1C26ZIEP1YWT2AXUHFXVN5683"

def get_miners(start_block, end_block, api_key):
    miners = set()

    for i in range(start_block, end_block + 1):
        temp_req = req.get("https://api.etherscan.io/api" + 
                            "?module=block" +
                            "&action=getblockreward" +
                            "&blockno=" + str(i) +
                            "&apikey=" + API_KEY)

        data = temp_req.json()

        if int(data['status']) == 1:
            miners.add(data["result"]["blockMiner"])
        else:
            print("Block", str(i), "is not ready")

    return miners


# ethereumetl export_blocks_and_transactions --start-block 0 --end-block 500 \
# --blocks-output blocks.csv --transactions-output transactions.csv \
# --provider-uri https://mainnet.infura.io/v3/6161de04e92d4a8e872fef998498440a