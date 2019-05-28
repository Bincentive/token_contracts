from eth_tester.backends.pyevm.main import (
    get_default_account_keys,
)

from tests.utils.ecrecover import (
    to_eth_signed_message_hash,
)
from tests.utils.transfer import (
    presigned_transfer,
)


def test_initial_amount(w3, BCNTToken, Bincentive):
    assert BCNTToken.functions.balanceOf(Bincentive).call() == 1000000000 * (10 ** 18)


def test_transfer(w3, BCNTToken, Bincentive):
    owner_account = Bincentive
    receiver_account = w3.eth.accounts[1]
    transfer_amount = 1000000000
    previous_receiver_balance = BCNTToken.functions.balanceOf(receiver_account).call()
    previous_owner_balance = BCNTToken.functions.balanceOf(owner_account).call()

    tx_hash = BCNTToken.functions.transfer(receiver_account, transfer_amount).transact({
        'from': owner_account,
        'gas': 300000,
    })
    w3.testing.mine(1)

    receipt = w3.eth.waitForTransactionReceipt(tx_hash)
    assert BCNTToken.events.Transfer().processReceipt(receipt)[0]['args']['from'] == owner_account
    assert BCNTToken.events.Transfer().processReceipt(receipt)[0]['args']['to'] == receiver_account

    receiver_balance = BCNTToken.functions.balanceOf(receiver_account).call()
    owner_balance = BCNTToken.functions.balanceOf(owner_account).call()

    assert previous_receiver_balance + transfer_amount == receiver_balance
    assert owner_balance + transfer_amount == previous_owner_balance


def test_transfer_with_insufficient_balance(w3, BCNTToken, Bincentive):
    owner_account = Bincentive
    receiver_account = w3.eth.accounts[1]
    max_amount = BCNTToken.functions.balanceOf(owner_account).call()
    tx_hash = BCNTToken.functions.transfer(receiver_account, max_amount + 1).transact({
        'from': owner_account,
        'gas': 300000,
    })
    w3.testing.mine(1)
    assert len(w3.eth.waitForTransactionReceipt(tx_hash)['logs']) == 0
    assert max_amount == BCNTToken.functions.balanceOf(owner_account).call()


def test_presigned_transfer(w3, BCNTToken, Bincentive, Bincentive_account_index):
    owner_account = Bincentive
    owner_priv_key = get_default_account_keys()[Bincentive_account_index]
    receiver_account = w3.eth.accounts[1]
    relayer_account = w3.eth.accounts[2]
    transfer_amount = 1000000000
    fee_amount = 1000
    previous_receiver_balance = BCNTToken.functions.balanceOf(receiver_account).call()
    previous_owner_balance = BCNTToken.functions.balanceOf(owner_account).call()

    tx_hash = presigned_transfer(
        w3=w3,
        BCNTToken=BCNTToken,
        private_key=owner_priv_key,
        receiver_account=receiver_account,
        transfer_amount=transfer_amount,
        fee_amount=fee_amount,
        nonce=0,
        duration=20,
        relayer_account=relayer_account,
    )
    w3.testing.mine(1)

    receipt = w3.eth.waitForTransactionReceipt(tx_hash)
    assert BCNTToken.events.Transfer().processReceipt(receipt)[0]['args']['from'] == owner_account
    assert BCNTToken.events.Transfer().processReceipt(receipt)[0]['args']['to'] == receiver_account
    assert BCNTToken.events.Transfer().processReceipt(receipt)[1]['args']['from'] == owner_account
    assert BCNTToken.events.Transfer().processReceipt(receipt)[1]['args']['to'] == relayer_account
    assert BCNTToken.events.TransferPreSigned().processReceipt(
        receipt)[0]['args']['amount'] == transfer_amount
    assert BCNTToken.events.TransferPreSigned().processReceipt(
        receipt)[0]['args']['fee'] == fee_amount

    receiver_balance = BCNTToken.functions.balanceOf(receiver_account).call()
    owner_balance = BCNTToken.functions.balanceOf(owner_account).call()
    relayer_balance = BCNTToken.functions.balanceOf(relayer_account).call()

    assert previous_receiver_balance + transfer_amount == receiver_balance
    assert owner_balance + transfer_amount + fee_amount == previous_owner_balance
    assert relayer_balance == fee_amount


def test_parallelized_presigned_transfer(w3, BCNTToken, Bincentive, Bincentive_account_index):
    owner_account = Bincentive
    owner_priv_key = get_default_account_keys()[Bincentive_account_index]
    receiver_account = w3.eth.accounts[1]
    transfer_amount = 1000000000
    fee_amount = 1000
    previous_receiver_balance = BCNTToken.functions.balanceOf(receiver_account).call()
    previous_owner_balance = BCNTToken.functions.balanceOf(owner_account).call()

    presigned_transfer(
        w3=w3,
        BCNTToken=BCNTToken,
        private_key=owner_priv_key,
        receiver_account=receiver_account,
        transfer_amount=transfer_amount,
        fee_amount=fee_amount,
        nonce=0,
        duration=20,
        relayer_account=w3.eth.accounts[2],
    )
    presigned_transfer(
        w3=w3,
        BCNTToken=BCNTToken,
        private_key=owner_priv_key,
        receiver_account=receiver_account,
        transfer_amount=transfer_amount,
        fee_amount=fee_amount,
        nonce=1,
        duration=20,
        relayer_account=w3.eth.accounts[4],
    )
    presigned_transfer(
        w3=w3,
        BCNTToken=BCNTToken,
        private_key=owner_priv_key,
        receiver_account=receiver_account,
        transfer_amount=transfer_amount,
        fee_amount=fee_amount,
        nonce=2,
        duration=20,
        relayer_account=w3.eth.accounts[5],
    )
    w3.testing.mine(1)

    receiver_balance = BCNTToken.functions.balanceOf(receiver_account).call()
    owner_balance = BCNTToken.functions.balanceOf(owner_account).call()

    assert previous_receiver_balance + 3 * transfer_amount == receiver_balance
    assert owner_balance + 3 * transfer_amount + 3 * fee_amount == previous_owner_balance


def test_expired_presigned_transfer(w3, BCNTToken, Bincentive, Bincentive_account_index):
    owner_account = Bincentive
    owner_priv_key = get_default_account_keys()[Bincentive_account_index]
    receiver_account = w3.eth.accounts[1]
    relayer_account = w3.eth.accounts[2]
    transfer_amount = 1000000000
    fee_amount = 1000
    previous_receiver_balance = BCNTToken.functions.balanceOf(receiver_account).call()
    previous_owner_balance = BCNTToken.functions.balanceOf(owner_account).call()

    nonce = 0
    block_number = w3.eth.blockNumber
    hashedTx = BCNTToken.functions.transferPreSignedHashing(
        BCNTToken.address,
        receiver_account,
        transfer_amount,
        fee_amount,
        nonce,
        block_number + 5,
    ).call()
    signature = owner_priv_key.sign_msg_hash(
        to_eth_signed_message_hash(hashedTx)
    ).to_bytes()

    w3.testing.mine(6)
    BCNTToken.functions.transferPreSigned(
        signature,
        receiver_account,
        transfer_amount,
        fee_amount,
        nonce,
        block_number + 5,
    ).transact({'from': relayer_account, 'gas': 300000})
    w3.testing.mine(1)
    receiver_balance = BCNTToken.functions.balanceOf(receiver_account).call()
    owner_balance = BCNTToken.functions.balanceOf(owner_account).call()
    relayer_balance = BCNTToken.functions.balanceOf(relayer_account).call()

    assert receiver_balance == previous_receiver_balance
    assert owner_balance == previous_owner_balance
    assert relayer_balance == 0


def test_presigned_transfer_with_wrong_signature(w3, BCNTToken, Bincentive):
    owner_account = Bincentive
    wrong_owner_priv_key = get_default_account_keys()[1]
    receiver_account = w3.eth.accounts[1]
    relayer_account = w3.eth.accounts[2]
    transfer_amount = 1000000000
    fee_amount = 1000
    previous_receiver_balance = BCNTToken.functions.balanceOf(receiver_account).call()
    previous_owner_balance = BCNTToken.functions.balanceOf(owner_account).call()

    tx_hash = presigned_transfer(
        w3=w3,
        BCNTToken=BCNTToken,
        private_key=wrong_owner_priv_key,
        receiver_account=receiver_account,
        transfer_amount=transfer_amount,
        fee_amount=fee_amount,
        nonce=0,
        duration=20,
        relayer_account=relayer_account,
    )
    w3.testing.mine(1)

    receiver_balance = BCNTToken.functions.balanceOf(receiver_account).call()
    owner_balance = BCNTToken.functions.balanceOf(owner_account).call()

    assert len(w3.eth.waitForTransactionReceipt(tx_hash)['logs']) == 0
    assert receiver_balance == previous_receiver_balance
    assert owner_balance == previous_owner_balance


def test_presigned_transfer_with_same_signature(
        w3, BCNTToken, Bincentive, Bincentive_account_index):
    owner_account = Bincentive
    owner_priv_key = get_default_account_keys()[Bincentive_account_index]
    receiver_account = w3.eth.accounts[1]
    transfer_amount = 1000000000
    previous_balance = BCNTToken.functions.balanceOf(receiver_account).call()

    nonce = 0
    block_number = w3.eth.blockNumber
    hashedTx = BCNTToken.functions.transferPreSignedHashing(
        BCNTToken.address,
        receiver_account,
        transfer_amount,
        0,
        nonce,
        block_number + 20,
    ).call()
    signature = owner_priv_key.sign_msg_hash(
        to_eth_signed_message_hash(hashedTx)
    ).to_bytes()
    BCNTToken.functions.transferPreSigned(
        signature,
        receiver_account,
        transfer_amount,
        0,
        nonce,
        block_number + 20,
    ).transact({'from': owner_account, 'gas': 300000})
    w3.testing.mine(1)
    after_balance = BCNTToken.functions.balanceOf(receiver_account).call()
    assert previous_balance + transfer_amount == after_balance
    BCNTToken.functions.transferPreSigned(
        signature,
        receiver_account,
        transfer_amount,
        0,
        nonce,
        block_number + 20,
    ).transact({'from': owner_account, 'gas': 300000})
    w3.testing.mine(1)
    assert after_balance == BCNTToken.functions.balanceOf(receiver_account).call()


def test_presigned_transfer_with_insufficient_balance(w3, BCNTToken):
    owner_account = w3.eth.accounts[1]
    owner_priv_key = get_default_account_keys()[1]
    receiver_account = w3.eth.accounts[2]
    relayer_account = w3.eth.accounts[2]
    transfer_amount = 1000000000
    fee_amount = 1000
    previous_receiver_balance = BCNTToken.functions.balanceOf(receiver_account).call()
    previous_owner_balance = BCNTToken.functions.balanceOf(owner_account).call()
    assert previous_owner_balance == 0

    tx_hash = presigned_transfer(
        w3=w3,
        BCNTToken=BCNTToken,
        private_key=owner_priv_key,
        receiver_account=receiver_account,
        transfer_amount=transfer_amount,
        fee_amount=fee_amount,
        nonce=0,
        duration=20,
        relayer_account=relayer_account,
    )
    w3.testing.mine(1)

    receiver_balance = BCNTToken.functions.balanceOf(receiver_account).call()
    owner_balance = BCNTToken.functions.balanceOf(owner_account).call()

    assert len(w3.eth.waitForTransactionReceipt(tx_hash)['logs']) == 0
    assert receiver_balance == previous_receiver_balance
    assert owner_balance == previous_owner_balance


def test_presigned_transfer_with_insufficient_balance_to_pay_fee(
        w3,
        BCNTToken,
        Bincentive,
        Bincentive_account_index):
    owner_account = Bincentive
    owner_priv_key = get_default_account_keys()[Bincentive_account_index]
    receiver_account = w3.eth.accounts[1]
    relayer_account = w3.eth.accounts[2]
    fee_amount = 1000
    previous_owner_balance = BCNTToken.functions.balanceOf(owner_account).call()
    previous_receiver_balance = BCNTToken.functions.balanceOf(receiver_account).call()
    previous_relayer_balance = BCNTToken.functions.balanceOf(relayer_account).call()

    tx_hash = presigned_transfer(
        w3=w3,
        BCNTToken=BCNTToken,
        private_key=owner_priv_key,
        receiver_account=receiver_account,
        transfer_amount=previous_owner_balance,
        fee_amount=fee_amount,
        nonce=0,
        duration=20,
        relayer_account=relayer_account,
    )
    w3.testing.mine(1)

    receiver_balance = BCNTToken.functions.balanceOf(receiver_account).call()
    owner_balance = BCNTToken.functions.balanceOf(owner_account).call()
    relayer_balance = BCNTToken.functions.balanceOf(relayer_account).call()

    assert len(w3.eth.waitForTransactionReceipt(tx_hash)['logs']) == 0
    assert receiver_balance == previous_receiver_balance
    assert owner_balance == previous_owner_balance
    assert relayer_balance == previous_relayer_balance
