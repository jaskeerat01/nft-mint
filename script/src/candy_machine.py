import constants
from aptos_sdk.async_client import RestClient, FaucetClient
from aptos_sdk.account import Account, AccountAddress, ed25519
from aptos_sdk.transactions import RawTransaction, SignedTransaction
from aptos_sdk.authenticator import Authenticator
from aptos_sdk.bcs import Serializer
import sys
import os
import json
import asyncio
from pick import pick
import util
import time
class CandyMachine:
    def __init__(self, mode, batch_num):
        self.mode = mode
        self.batch_num = batch_num
        self.node = None
        self.faucet = None
        self.account = None

        print(f"Mode: {self.mode}")
        print(f"Contract address: {constants.CONTRACT_ADDRESS}")

        if mode == 'dev':
            self.node = constants.DEV_NET_NODE
            self.faucet = constants.DEV_NET_FAUCET
        elif mode == 'test':
            self.node = constants.TEST_NET_NODE
            self.faucet = constants.TEST_NET_FAUCET
        else:
            self.node = constants.MAINNET_NODE

        self.rest_client = RestClient(self.node)
        if self.faucet:
            self.faucet_client = FaucetClient(self.faucet, self.rest_client)

        with open(os.path.join(sys.path[0], "config.json"), 'r') as f:
            config = json.load(f)

        self.asset_folder = config['collection']['assetDir']
        self.metadata_folder = config['collection']['metadataDir']
        self.collection_name = config['collection']['collectionName']
        self.collection_description = config['collection']['collectionDescription']
        self.collection_size = config['collection']['collectionSize']
        self.collection_cover = config['collection']['collectionCover']
        self.max_mint_per_wallet = int(config['collection']['maxMintPerWallet'])
        self.mint_fee = int(config['collection']['mintFee'])
        self.public_mint_time = int(config['collection']['publicMintTime'])
        self.presale_mint_time = int(config['collection']['presaleMintTime'])
        self.royalty_points_denominator = config['collection']['royalty_points_denominator']
        self.royalty_points_numerator = config['collection']['royalty_points_numerator']

    async def generate_new_account(self):
        account = Account.generate()
        with open(os.path.join(sys.path[0], "config.json"), 'r') as f:
            config = json.load(f)

        config['candymachine']['cmPublicKey'] = str(account.address())
        config['candymachine']['cmPrivateKey'] = account.private_key.hex()

        with open(os.path.join(sys.path[0], "config.json"), 'w') as f:
            json.dump(config, f, indent=4)

        self.account_addr = config['candymachine']['cmPublicKey']
        self.account_private = config['candymachine']['cmPrivateKey']

        return account

    async def get_existing_account(self):
        with open(os.path.join(sys.path[0], "config.json"), 'r') as f:
            config = json.load(f)

        self.account_addr = config['candymachine']['cmPublicKey']
        self.account_private = config['candymachine']['cmPrivateKey']

        if len(self.account_addr) != 66 or len(self.account_private) != 66:
            raise Exception("Invalid account keys in config file")

        account_addr = AccountAddress.from_str(self.account_addr)
        account_private = ed25519.PrivateKey(bytes.fromhex(self.account_private))

        return Account(account_addr, account_private)

    async def prepareAccount(self):
        """Prepares and funds the candy machine account."""
        with open(os.path.join(sys.path[0], "config.json"), 'r') as f:
            config = json.load(f)
        
        account = None
        
        if len(config['candymachine']['cmPublicKey']) == 66 and len(config['candymachine']['cmPrivateKey']) == 66:
            print("Candy machine addresses are already filled in config.json.")
            _, index = pick(["yes", "no"], "Do you wish to override them with new funded accounts?")
            if index == 1:
                account = await self.get_existing_account()
            else:
                account = await self.generate_new_account()
        else:
            account = await self.generate_new_account()
        
        if account is None:
            raise Exception("Failed to create or load account")

        print(f'Public key: {account.address()}')
        print(f'Private key: {account.private_key}')

        if self.mode == "dev":
            print("Airdropping 3 APT to your account on dev net...")
            for i in range(3):
                await self.faucet_client.fund_account(str(account.address()), 100_000_000)

        while True:
            answer = "yes" if self.mode == "dev" else input("Enter 'yes' if you have some aptos in the account: ")
            if answer == "yes":
                try:
                    print(f"Checking account address {account.address()}...")
                    account_balance = await self.rest_client.account_balance(account.address())
                    account_balance = int(account_balance)

                except Exception as e:
                    print(f"Error: {e}")
                    print("Please add some Aptos to your candy machine account and try again.")
                    raise Exception("Not enough funds in account")
                
                if account_balance > 2000:
                    print(f'Balance: {account_balance}\n')
                    break
            else:
                continue

        self.account = account

    async def create(self):
        """Creates the candy machine contract and initializes it."""
        print("\n=== Preparing candy machine account ===")
        await self.prepareAccount()

        print("\n=== Verifying assets and metadata ===")
        if not util.verifyMetadataFiles():
            return

        print('\n=== Upload assets to storage solution ===')
        if not util.uploadFolder():
            print("Not all files were uploaded to storage. Try again.")
            return

        await self.createCandyMachine()
        await self.createCollection()

        txn_payload = {
            "function": f"{constants.CONTRACT_ADDRESS}::ftmpad::mint_tokens",
            "type_arguments": [],
            "arguments": [
                str(self.account.address()),
                self.collection_name,
                "2"
            ],
            "type": "entry_function_payload"
        }
        sender_address = self.account.address()
        account_data = await self.rest_client.account(sender_address)
        sequence_number = int(account_data["sequence_number"])
        raw_txn = RawTransaction(
        sender=sender_address,
        sequence_number=sequence_number,
        payload=txn_payload,
        max_gas_amount=1000,
        gas_unit_price=1,
        expiration_timestamp_secs=int(time.time()) + 600,  # Expires in 10 minutes
        chain_id=4  # Change if needed
)
        signature = self.account.sign(raw_txn)
        signed_txn = SignedTransaction(raw_txn, Authenticator.ed25519(self.account.public_key(), signature))

        txn_hash = await self.rest_client.submit_bcs_transaction(signed_txn)
        await self.rest_client.wait_for_transaction(txn_hash)
        print(f"Transaction submitted: {txn_hash}")

        await self.uploadNftsToCm()
        await self.update_presale_mint_time()
        await self.update_public_mint_time()
        await self.update_mint_fee()

    async def createCandyMachine(self):
        """Creates the candy machine smart contract."""
        print("\n=== Deploying Candy Machine Contract ===")
        txn_payload = {
            "function": f"{constants.CONTRACT_ADDRESS}::ftmpad::initialize_candy_machine",
            "type_arguments": [],
            "arguments": [
                self.collection_name,
                self.collection_description,
                self.collection_size,
                self.max_mint_per_wallet,
                self.mint_fee
            ],
            "type": "entry_function_payload"
        }

        txn_hash = await self.rest_client.submit_bcs_transaction(txn_payload)
        await self.rest_client.wait_for_transaction(txn_hash)
        print(f"Candy Machine Created: {txn_hash}")

        # Example transaction payload (modify as per your contract)
        txn_payload = {
            "function": f"{constants.CONTRACT_ADDRESS}::ftmpad::mint_tokens",
            "type_arguments": [],
            "arguments": [
                str(self.account.address()),
                self.collection_name,
                "2"  # Example argument
            ],
            "type": "entry_function_payload"
        }

        txn_hash = await self.rest_client.submit_transaction(self.account, txn_payload)
        await self.rest_client.wait_for_transaction(txn_hash)
        print(f"Transaction submitted: {txn_hash}")

        await self.uploadNftsToCm()
        await self.update_presale_mint_time()
        await self.update_public_mint_time()
        await self.update_mint_fee()

    async def retryFailedUploads(self):
        self.account = await self.get_existing_account()
        if len(self.account_addr) != 66 or len(self.account_private) != 66:
            print("Can't continue upload as CM info is not valid in config file")
            return

        await self.uploadNftsToCm()

    async def update_mint_fee(self):
        print("\n=== Setting mint fee ===")
        txn_hash = await self.rest_client.set_mint_fee_per_mille(
            self.account, self.collection_name, self.mint_fee
        )
        await self.rest_client.wait_for_transaction(txn_hash)
        print("\nSuccess, mint fee is set to:", txn_hash)

    async def update_presale_mint_time(self):
        print("\n=== Setting presale mint time ===")
        txn_hash = await self.rest_client.set_presale_mint_time(
            self.account, self.collection_name, self.presale_mint_time
        )
        await self.rest_client.wait_for_transaction(txn_hash)
        print("\nSuccess, presale mint time set:", txn_hash)

    async def update_public_mint_time(self):
        print("\n=== Setting public mint time ===")
        txn_hash = await self.rest_client.set_public_mint_time(
            self.account, self.collection_name, self.public_mint_time
        )
        await self.rest_client.wait_for_transaction(txn_hash)
        print("\nSuccess, public mint time set:", txn_hash)