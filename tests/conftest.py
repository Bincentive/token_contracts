import os
import pytest

from web3 import (
    Web3,
)

from web3.providers.eth_tester import (
    EthereumTesterProvider,
)

from eth_tester import (
    EthereumTester,
    PyEVMBackend,
)

from eth_utils import (
    to_checksum_address
)
from eth_tester.backends.pyevm.main import (
    get_default_genesis_params,
    get_default_account_keys,
    generate_genesis_state,
)

from evm.db import (
    get_db_backend,
)

from evm.chains.tester import (
    MainnetTesterChain,
)

from solc import compile_files


DIR = os.path.dirname(__file__)


@pytest.fixture
def backend_with_configured_genesis():
    """
    Copied from setup_tester_chain() in eth_tester.backends.pyevm.main.
    By pass the default genesis settings.
    """
    backend = PyEVMBackend()

    genesis_params = get_default_genesis_params()
    account_keys = get_default_account_keys()
    genesis_state = generate_genesis_state(account_keys)

    base_db = get_db_backend()

    # Configure the genesis parameters
    genesis_params['gas_limit'] = 10000000

    chain = MainnetTesterChain.from_genesis(base_db, genesis_params, genesis_state)
    backend.chain = chain

    return backend


@pytest.fixture
def eth_tester(backend_with_configured_genesis):
    return EthereumTester(
        # backend=PyEVMBackend(),
        backend=backend_with_configured_genesis,
    )


@pytest.fixture
def w3(eth_tester):
    eth_tester.disable_auto_mine_transactions()
    # Set up we3 provider
    provider = EthereumTesterProvider(eth_tester)
    web3 = Web3(provider)
    if hasattr(web3.eth, "enable_unaudited_features"):
        web3.eth.enable_unaudited_features()

    return web3


@pytest.fixture
def Bincentive_account_index():
    return 9


@pytest.fixture
def Bincentive(w3, Bincentive_account_index):
    return w3.eth.accounts[Bincentive_account_index]


@pytest.fixture
def BCNTToken(w3, Bincentive):
    contract_path = os.path.join(DIR, '../contracts/BCNTToken.sol')
    compiled_sol = compile_files([contract_path])
    contract_interface = compiled_sol['%s:BCNTToken' % contract_path]
    contract = w3.eth.contract(abi=contract_interface['abi'], bytecode=contract_interface['bin'])

    private_contract_path = os.path.join(DIR, '../contracts/PrivateToken.sol')
    private_compiled_sol = compile_files([private_contract_path])
    private_contract_interface = private_compiled_sol['%s:PrivateToken' % private_contract_path]

    # Get transaction hash from deployed contract
    # constructor_kwargs = {}
    # tx_hash = contract.constructor(**constructor_kwargs).transact()

    # Sender and admin would be different account in practice.
    tx_hash = contract.constructor(Bincentive).transact(
        {'from': w3.eth.accounts[0], 'gas': 5000000}
    )
    w3.testing.mine(1)
    contract_address = w3.eth.waitForTransactionReceipt(tx_hash)['contractAddress']
    contract_instance = w3.eth.contract(
        address=contract_address,
        abi=contract_interface['abi'],
    )
    assert w3.eth.getCode(contract_address) != b''

    private_contract_address = to_checksum_address(
        contract_instance.functions.privateToken().call())
    private_contract_instance = w3.eth.contract(
        address=private_contract_address,
        abi=private_contract_interface['abi'],
    )

    _unlock_time = w3.eth.getBlock(w3.eth.blockNumber)['timestamp'] + 50000
    tx_hash = private_contract_instance.functions.startPublicSale(_unlock_time).transact({
        'from': Bincentive,
        'gas': 300000,
    })
    w3.testing.mine(1)
    w3.eth.waitForTransactionReceipt(tx_hash)

    tx_hash = private_contract_instance.functions.unLock().transact({
        'from': Bincentive,
        'gas': 300000,
    })
    w3.testing.mine(1)
    w3.eth.waitForTransactionReceipt(tx_hash)

    tx_hash = private_contract_instance.functions.deposit(Bincentive).transact({
        'from': Bincentive,
        'gas': 300000,
    })
    w3.testing.mine(1)
    w3.eth.waitForTransactionReceipt(tx_hash)

    return contract_instance


@pytest.fixture
def PrivateBCNTToken(w3, Bincentive):
    contract_path = os.path.join(DIR, '../contracts/BCNTToken.sol')
    compiled_sol = compile_files([contract_path])
    contract_interface = compiled_sol['%s:BCNTToken' % contract_path]
    contract = w3.eth.contract(abi=contract_interface['abi'], bytecode=contract_interface['bin'])

    # Get transaction hash from deployed contract
    # constructor_kwargs = {}
    # tx_hash = contract.constructor(**constructor_kwargs).transact()

    # Sender and admin would be different account in practice.
    tx_hash = contract.constructor(Bincentive).transact(
        {'from': w3.eth.accounts[0], 'gas': 5000000}
    )
    w3.testing.mine(1)
    contract_address = w3.eth.waitForTransactionReceipt(tx_hash)['contractAddress']
    contract_instance = w3.eth.contract(
        address=contract_address,
        abi=contract_interface['abi'],
    )

    assert w3.eth.getCode(contract_address) != b''

    return contract_instance


@pytest.fixture
def PrivateToken(w3, PrivateBCNTToken):
    contract_path = os.path.join(DIR, '../contracts/PrivateToken.sol')
    compiled_sol = compile_files([contract_path])
    contract_interface = compiled_sol['%s:PrivateToken' % contract_path]

    contract_address = to_checksum_address(
        PrivateBCNTToken.functions.privateToken().call())
    contract_instance = w3.eth.contract(
        address=contract_address,
        abi=contract_interface['abi'],
    )
    assert w3.eth.getCode(contract_address) != b''

    return contract_instance
