x=1
while [ $x -le 5 ]
do
    curl https://juno-rpc-cache.reece.sh/abci_info? &
done


while true; do curl -d '{"jsonrpc":"2.0","id":542337771993,"method":"status","params":{}}' -H "Content-Type: application/json" -X POST https://juno-rpc-cache.reece.sh/; sleep 0.1; done