# test post so we can ensure it gets cached once I add that feature

curl -d '{"jsonrpc":"2.0","id":521627379779,"method":"abci_query","params":{"path":"/cosmwasm.wasm.v1.Query/SmartContractState","data":"0a3f6a756e6f31753735613372357973666d7475636e676d7930733574336a3076646c306e307175357668746339736a3576636c66706639367173656370367364120b7b22696e666f223a7b7d7d","prove":false}}' -H "Content-Type: application/json" -X POST https://rpc.juno.strange.love/

curl -d '{"jsonrpc":"2.0","id":521627379779,"method":"abci_query","params":{"path":"/cosmwasm.wasm.v1.Query/SmartContractState","data":"0a3f6a756e6f31753735613372357973666d7475636e676d7930733574336a3076646c306e307175357668746339736a3576636c66706639367173656370367364120b7b22696e666f223a7b7d7d","prove":false}}' -H "Content-Type: application/json" -X POST http://localhost:5001
