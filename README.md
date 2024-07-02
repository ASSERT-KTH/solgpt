# solgpt
A pipeline to fix bugged Solidity smart contract with ChatGPT.


Make sure to have the [Slither](https://github.com/crytic/slither) docker image installed locally.

## Installation
```bash
docker pull trailofbits/eth-security-toolbox
pip install -r requirements.txt
export TOKEN_AI='<Openai API KEY>'
```

## Usage
Place the smart contract in `cleaned` folder and run the following command:
```bash
python solgpt_get_fix.py
```