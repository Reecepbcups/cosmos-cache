# git checkout v12.0.0-beta.1 && make install
CHAIN_ID="uni-6"
# NODE="--node https://uni-rpc.reece.sh:443"
NODE="--node http://127.0.0.1:5001"
KEY="juno2"
export KEYRING=${KEYRING:-"test"}
export KEYALGO="secp256k1"

# This is a test account found in juno/scripts/test_node.sh :)
# juno1efd63aw40lxf3n4mhf7dzhjkr453axurv2zdzk
echo "wealth flavor believe regret funny network recall kiss grape useless pepper cram hint member few certain unveil rather brick bargain curious require crowd raise" | junod keys add $KEY --keyring-backend $KEYRING --algo $KEYALGO --recover

junod q gov params $NODE

junod q bank balances juno1efd63aw40lxf3n4mhf7dzhjkr453axurv2zdzk $NODE

junod tx bank send $KEY juno1efd63aw40lxf3n4mhf7dzhjkr453axurv2zdzk 1ujunox --keyring-backend $KEYRING --chain-id $CHAIN_ID $NODE --fees 500ujunox
# junod q tx  $NODE

export JUNOD_COMMAND_ARGS="--from $KEY $NODE -b block --output json --yes --chain-id $CHAIN_ID --gas 1000000 --fees 2500ujunox --keyring-backend $KEYRING"

# junod tx wasm store ./test/cw_template.wasm --from juno1 --node http://localhost:5001 --keyring-backend test --chain-id uni-6

function upload_and_init () {
    ADMIN=$1    

    # cw_template = the basic counter contract
    echo "Uploading example contract to chain store"
    junod tx wasm store ./test/cw_template.wasm $JUNOD_COMMAND_ARGS
}