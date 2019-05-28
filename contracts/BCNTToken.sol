pragma solidity ^0.4.24;
import "./DepositFromPrivateToken.sol";
import "./ECRecovery.sol";

contract BCNTToken is DepositFromPrivateToken{
    using SafeMath for uint256;

    string public constant name = "Bincentive Token"; // Storage slot 4 // solium-disable-line uppercase
    string public constant symbol = "BCNT"; // Storage slot 5 // solium-disable-line uppercase
    uint8 public constant decimals = 18; // Storage slot 6 // solium-disable-line uppercase
    uint256 public constant INITIAL_SUPPLY = 1000000000 * (10 ** uint256(decimals)); // Storage slot 7
    mapping(bytes => bool) internal signatures; // Storage slot 8
    event TransferPreSigned(address indexed from, address indexed to, address indexed delegate, uint256 amount, uint256 fee);

    /**
    * @notice Submit a presigned transfer
    * @param _signature bytes The signature, issued by the owner.
    * @param _to address The address which you want to transfer to.
    * @param _value uint256 The amount of tokens to be transferred.
    * @param _fee uint256 The amount of tokens paid to msg.sender, by the owner.
    * @param _nonce uint256 Presigned transaction number.
    * @param _validUntil uint256 Block number until which the presigned transaction is still valid.
    */
    function transferPreSigned(
        bytes _signature,
        address _to,
        uint256 _value,
        uint256 _fee,
        uint256 _nonce,
        uint256 _validUntil
    )
        public
        returns (bool)
    {
        require(_to != address(0));
        require(signatures[_signature] == false);
        require(block.number <= _validUntil);

        bytes32 hashedTx = ECRecovery.toEthSignedMessageHash(
          transferPreSignedHashing(address(this), _to, _value, _fee, _nonce, _validUntil)
        );

        address from = ECRecovery.recover(hashedTx, _signature);

        balances[from] = balances[from].sub(_value).sub(_fee);
        balances[_to] = balances[_to].add(_value);
        balances[msg.sender] = balances[msg.sender].add(_fee);
        signatures[_signature] = true;

        emit Transfer(from, _to, _value);
        emit Transfer(from, msg.sender, _fee);
        emit TransferPreSigned(from, _to, msg.sender, _value, _fee);
        return true;
    }

    /**
    * @notice Hash (keccak256) of the payload used by transferPreSigned
    * @param _token address The address of the token.
    * @param _to address The address which you want to transfer to.
    * @param _value uint256 The amount of tokens to be transferred.
    * @param _fee uint256 The amount of tokens paid to msg.sender, by the owner.
    * @param _nonce uint256 Presigned transaction number.
    * @param _validUntil uint256 Block number until which the presigned transaction is still valid.
    */
    function transferPreSignedHashing(
        address _token,
        address _to,
        uint256 _value,
        uint256 _fee,
        uint256 _nonce,
        uint256 _validUntil
    )
        public
        pure
        returns (bytes32)
    {
        /* "0d2d1bf5": transferPreSigned(address,address,uint256,uint256,uint256,uint256) */
        return keccak256(
            abi.encodePacked(
                bytes4(0x0a0fb66b),
                _token,
                _to,
                _value,
                _fee,
                _nonce,
                _validUntil
            )
        );
    }

    /**
    * @dev Constructor that gives _owner all of existing tokens.
    */
    constructor(address _admin) public {
        totalSupply_ = INITIAL_SUPPLY;
        privateToken = new PrivateToken(
          _admin, "Bincentive Private Token", "BCNP", decimals, INITIAL_SUPPLY
       );
    }
}
