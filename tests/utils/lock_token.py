def start_public_sale(w3, PrivateToken, Bincentive):
    _unlock_time = w3.eth.getBlock(w3.eth.blockNumber)['timestamp'] + 50000
    tx_hash = PrivateToken.functions.startPublicSale(_unlock_time).transact(
        {'from': Bincentive, 'gas': 300000})
    w3.testing.mine(1)
    receipt = w3.eth.waitForTransactionReceipt(tx_hash)
    assert PrivateToken.events.StartPublicSale().processReceipt(
        receipt)[0]['event'] == 'StartPublicSale'


def unlock(w3, PrivateToken, Bincentive):
    tx_hash = PrivateToken.functions.unLock().transact({'from': Bincentive, 'gas': 300000})
    w3.testing.mine(1)
    w3.eth.waitForTransactionReceipt(tx_hash)
