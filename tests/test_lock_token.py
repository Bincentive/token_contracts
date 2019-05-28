from tests.utils.lock_token import start_public_sale, unlock


def test_origin_settings(w3, PrivateToken, Bincentive):
    admin_balance = PrivateToken.functions.balanceOf(Bincentive).call()
    decimals = PrivateToken.functions.decimals().call()
    symbol = PrivateToken.functions.symbol().call()
    token_name = PrivateToken.functions.name().call()

    assert token_name == 'Bincentive Private Token'
    assert symbol == 'BCNP'
    assert decimals == 18
    assert admin_balance == 1000000000 * (10 ** decimals)


def test_transfer_private(w3, PrivateToken, Bincentive):
    receiver_account = w3.eth.accounts[0]
    transfer_amount = 1000000000

    previous_receiver_balance = PrivateToken.functions.balanceOf(receiver_account).call()
    previous_owner_balance = PrivateToken.functions.balanceOf(Bincentive).call()

    PrivateToken.functions.transfer(receiver_account, transfer_amount).transact({
        'from': Bincentive,
        'gas': 300000,
    })
    w3.testing.mine(1)

    receiver_balance = PrivateToken.functions.balanceOf(receiver_account).call()
    owner_balance = PrivateToken.functions.balanceOf(Bincentive).call()

    assert previous_receiver_balance + transfer_amount == receiver_balance
    assert owner_balance + transfer_amount == previous_owner_balance


def test_deposit_before_public_sale_start(w3, PrivateToken, PrivateBCNTToken, Bincentive):
    receiver_account = w3.eth.accounts[0]
    transfer_amount = 1000000000

    PrivateToken.functions.transfer(receiver_account, transfer_amount).transact({
        'from': Bincentive,
        'gas': 300000,
    })
    w3.testing.mine(1)

    sender_account = receiver_account
    tx_hash = PrivateToken.functions.deposit(sender_account).transact(
        {'from': sender_account, 'gas': 300000}
    )
    w3.testing.mine(1)
    receipt = w3.eth.waitForTransactionReceipt(tx_hash)
    assert len(receipt.logs) == 0

    sender_balance = PrivateBCNTToken.functions.balanceOf(sender_account).call()
    sender_origin_balance = PrivateToken.functions.balanceOf(sender_account).call()
    assert sender_balance == 0
    assert sender_origin_balance == transfer_amount


def test_deposit_from_admin_after_public_sale(w3, PrivateToken, PrivateBCNTToken, Bincentive):
    start_public_sale(w3, PrivateToken, Bincentive)

    previous_origin_owner_balance = PrivateToken.functions.balanceOf(Bincentive).call()
    previous_owner_balance = PrivateBCNTToken.functions.balanceOf(Bincentive).call()

    tx_hash = PrivateToken.functions.deposit(Bincentive).transact(
        {'from': Bincentive, 'gas': 300000}
    )
    w3.testing.mine(1)
    receipt = w3.eth.waitForTransactionReceipt(tx_hash)
    event = PrivateToken.events.Deposit().processReceipt(receipt)
    assert event[0].event == 'Deposit'

    origin_owner_balance = PrivateToken.functions.balanceOf(Bincentive).call()
    owner_balance = PrivateBCNTToken.functions.balanceOf(Bincentive).call()

    assert owner_balance == previous_origin_owner_balance
    assert previous_owner_balance == 0
    assert origin_owner_balance == 0


def test_deposit_after_unlock(w3, PrivateToken, PrivateBCNTToken, Bincentive):
    receiver_account = w3.eth.accounts[0]
    transfer_amount = 1000000000

    tx_hash = PrivateToken.functions.transfer(
        receiver_account, transfer_amount).transact({'from': Bincentive, 'gas': 300000})
    w3.testing.mine(1)
    start_public_sale(w3, PrivateToken, Bincentive)
    unlock(w3, PrivateToken, Bincentive)

    sender_account = receiver_account
    sender_origin_balance = PrivateToken.functions.balanceOf(sender_account).call()
    tx_hash = PrivateToken.functions.deposit(sender_account).transact(
        {'from': sender_account, 'gas': 300000}
    )
    w3.testing.mine(1)
    receipt = w3.eth.waitForTransactionReceipt(tx_hash)
    event = PrivateToken.events.Deposit().processReceipt(receipt)
    assert event[0].event == 'Deposit'

    sender_balance = PrivateBCNTToken.functions.balanceOf(sender_account).call()
    assert sender_origin_balance == sender_balance


def test_deposit_from_other_after_unlock(w3, PrivateToken, PrivateBCNTToken, Bincentive):
    receiver_account = w3.eth.accounts[0]
    someone = w3.eth.accounts[1]
    transfer_amount = 1000000000

    tx_hash = PrivateToken.functions.transfer(
        receiver_account, transfer_amount).transact({'from': Bincentive, 'gas': 300000})
    w3.testing.mine(1)
    start_public_sale(w3, PrivateToken, Bincentive)
    unlock(w3, PrivateToken, Bincentive)

    sender_account = receiver_account
    sender_origin_balance = PrivateToken.functions.balanceOf(sender_account).call()
    tx_hash = PrivateToken.functions.deposit(sender_account).transact(
        {'from': someone, 'gas': 300000}
    )
    w3.testing.mine(1)
    receipt = w3.eth.waitForTransactionReceipt(tx_hash)
    deposit_event = PrivateToken.events.Deposit().processReceipt(receipt)
    assert deposit_event[0].event == 'Deposit'

    transfer_events = PrivateToken.events.Transfer().processReceipt(receipt)

    # The first event is of BCNT and second one is of BCNP
    assert transfer_events[0].args['to'] == sender_account
    assert transfer_events[0].args['value'] == transfer_amount
    assert transfer_events[0].address == PrivateBCNTToken.address

    assert transfer_events[1].args['from'] == sender_account
    assert transfer_events[1].args['value'] == transfer_amount
    assert transfer_events[1].address == PrivateToken.address

    sender_balance = PrivateBCNTToken.functions.balanceOf(sender_account).call()
    assert sender_origin_balance == sender_balance
