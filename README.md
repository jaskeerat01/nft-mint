

# What is this ?

The Aptos NFT Mint project is designed to let creators set up a candymachine for NFT minting and a minting website ultra fast on Aptos. Candy machine is originally from Solana. We use Candy machine here to refer to general nft minting system on blockchain. 



## Features developed
* Set start and finish time for everyone.
* Won't accept your funds if they're out of NFTs to sell.
* Wallet based whitelist.
* Royalties for your NFT.
* Asset upload on IPFS.

## Preparations
In order to use this tool, here are the few things you need to have before continuing:

### Code 
```sh
git clone https://github.com/FTM-Labs/AptosNFTMint.git
```
### Python3
You need python version 3.9 and above.
https://www.python.org/downloads/ 
### Install dependencies
You need python version 3.9 and above

```sh
cd script/third_party
pip3 install -r requirements.txt
```
### nodeJs and npm 
https://docs.npmjs.com/downloading-and-installing-node-js-and-npm

Basically, you need layered art and use hashlips the generate images and metadata.

The metadata format we need is super simple. (the metadata format you generated from hashlips will work, we will just ignore the extra fields.)
However, make sure each metadata file has a different, unique name.
```json
{
  "name": "NFT NAME",
  "description": "NFT description",
  "attributes": [
    { "trait_type": "Background", "value": "Black" },
    { "trait_type": "Eyeball", "value": "Red" },
    { "trait_type": "Eye color", "value": "Yellow" },
    { "trait_type": "Iris", "value": "Small" },
    { "trait_type": "Shine", "value": "Shapes" },
    { "trait_type": "Bottom lid", "value": "Low" },
    { "trait_type": "Top lid", "value": "Middle" }
  ]
}
```
After generated the metadata, put it in a separate folder than your images. The top level folder needs to be created like below:
```
Assets/  
├─ Images/  
|  |- cover.png
│  ├─ 1.png  
│  ├─ 2.png  
│  ├─ 3.png  
│  ├─ ...  
├─ metadata/  
│  ├─ 1.json  
│  ├─ 2.json  
│  ├─ ...  
```
where the `cover.png` is the cover image for the collection.

**The metadata and corresponding image should have the same name, eg: 1.png and 1.json**
# Aptos NFT Minting Setup Guide

## Cover Image
- Use `cover.png` as the collection cover.
- Image and metadata must share the same name (e.g., `1.png` and `1.json`).

## Aptos Wallet Setup
For **mainnet** and **testnet**, set up a wallet and fund it for transaction fees.

- **Martian Wallet**: [Install](https://chrome.google.com/webstore/detail/martian-aptos-wallet/efbglgofoippbgcjepnhiblaibcnclgk)
- **Petra Wallet**: [Install](https://chrome.google.com/webstore/detail/petra-aptos-wallet/ejjladinnckdgjemekebdpeokbikhfci)

## Metadata & Unique Names
- Ensure unique names for each NFT (to avoid minting issues).
- Metadata format checks are enabled by default but can be disabled in code.

---

## Collection Metadata Example
```json
"collection": {
    "assetDir": "/path/to/images",
    "metadataDir": "/path/to/metadata",
    "collectionName": "MyNFTCollection",
    "collectionDescription": "Description",
    "collectionCover": "/path/to/cover.png",
    "collectionSize": 10,
    "maxMintPerWallet": 5,
    "mintFee": 100000000,
    "royalty_points_denominator": 1000,
    "royalty_points_numerator": 50,
    "presaleMintTime": 1630000000,
    "publicMintTime": 1640000000,
    "whitelistDir": "/path/to/whitelist.txt"
}
```
assetDir: Path to images.
metadataDir: Path to metadata.
collectionName: Name of the collection.
collectionCover: Path to cover image.
mintFee: Set minting cost (100000000 = 1 APT).

Whitelist File
Example format:
0x6c4e890a882b013f82a65db9b917a6d285caa892e46f2d93808b56f2aab2dd92 2
0x9d40f83eee59912bed7488d49becd5274ec21c66c40931c9db95a501e03ecee2 3

```0xAddress1 2
0xAddress2 3
```
###Candy Machine Configuration
json

"candymachine": {
    "cmPublicKey": "your-public-key",
    "cmPrivateKey": "your-private-key"
}

On devnet/testnet, leave the keys blank.
On mainnet, use the public/private key of your funded account.
##Storage Setup
For Pinata:

json

"storage": {
    "solution": "pinata",
    "pinata": {
        "pinataApi": "https://api.pinata.cloud/pinning/pinFileToIPFS",
        "pinataPublicKey": "your-public-key",
        "pinataSecretKey": "your-secret-key"
    }
}
Pinata: Register at Pinata, generate keys, and add them to config.json.
Switch Network
Set network mode in constants.py:

'test' for testnet, 'dev' for devnet, 'mainnet' for mainnet.
Ensure the mode matches in candyMachineInfo.js.
Create Candy Machine
Run in the src folder:
bash

```python3 cli.py```
Follow the prompts to create the candy machine.

Update Settings
Modify config.json to update presale mint time, mint fee, or whitelist. Re-run the commands to apply changes.

Create Website
Modify mint-site/helpers/candyMachineInfo.js:



Troubleshooting
ERESOURCE_ACCOUNT_EXISTS: Occurs if a wallet already holds a resource account. Retry uploads or move funds to a new wallet.

