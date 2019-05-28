from .ecrecover import to_eth_signed_message_hash


def presigned_transfer(
        w3,
        BCNTToken,
        private_key,
        receiver_account,
        transfer_amount,
        fee_amount,
        nonce,
        duration,
        relayer_account):
    block_number = w3.eth.blockNumber
    hashedTx = BCNTToken.functions.transferPreSignedHashing(
        BCNTToken.address,
        receiver_account,
        transfer_amount,
        fee_amount,
        nonce,
        block_number + duration,
    ).call()
    signature = private_key.sign_msg_hash(to_eth_signed_message_hash(hashedTx)).to_bytes()
    return BCNTToken.functions.transferPreSigned(
        signature,
        receiver_account,
        transfer_amount,
        fee_amount,
        nonce,
        block_number + duration,
    ).transact({'from': relayer_account, 'gas': 300000})
