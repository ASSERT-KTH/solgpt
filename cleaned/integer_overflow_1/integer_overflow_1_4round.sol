pragma solidity ^0.4.15;

contract Overflow {
    uint private sellerBalance = 0;

    function add(uint value) public returns (bool) {
        require(sellerBalance + value >= sellerBalance); // Check for overflow
        sellerBalance += value;
        return true;
    }
}