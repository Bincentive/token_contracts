#### Backup BCNT contract based on Zepplin contracts

##### Zepplin ERC20 contracts
- https://github.com/OpenZeppelin/openzeppelin-solidity/tree/602d9d988498822361c4f579cff4ee7080cd7e50/contracts/token/ERC20
- IERC20.sol
- ERC20.sol
- ERC20Detailed.sol
- ERC20Mintable.sol
- ERC20Burnable.sol
- **NOTE**:
    - variables in ERC20.sol: `_balances`, `_allowances` and `_totalSupply` are changed to type `internal`
    so that the BCNT contract inherit from it can update these variables.

##### Zepplin access control contracts
- https://github.com/OpenZeppelin/openzeppelin-solidity/tree/602d9d988498822361c4f579cff4ee7080cd7e50/contracts/access
- Roles.sol
- MinterRole.sol

##### Zepplin SafeMath contract
- https://github.com/OpenZeppelin/openzeppelin-solidity/tree/602d9d988498822361c4f579cff4ee7080cd7e50/contracts/math

##### Zepplin ECDSA contract
- https://github.com/OpenZeppelin/openzeppelin-solidity/tree/602d9d988498822361c4f579cff4ee7080cd7e50/contracts/cryptography

