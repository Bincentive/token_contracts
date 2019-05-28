from eth_utils import crypto


def to_eth_signed_message_hash(hashedMsg):
    if hashedMsg[:2] == '0x':
        hashedMsg = bytes.fromhex(hashedMsg[2:])
    prefix = '\x19Ethereum Signed Message:\n32'.encode('utf-8')
    return crypto.keccak_256(prefix + hashedMsg)
