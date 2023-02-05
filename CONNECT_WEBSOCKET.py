import json

import rel
import websocket

from CONFIG import RPC_WEBSOCKET

SUBSCRIBE_MSG = '{"jsonrpc": "2.0", "method": "subscribe", "params": ["tm.event=\'NewBlock\'"], "id": 1}'

# on a new block message, we will clear redis of any values which the config set to -2
def on_message(ws, message):
    # Use this for an indexer too? :D

    msg = json.loads(message)

    if msg.get("result") == {}:
        print("Subscribed to New Block...")
        return

    print(
        f"""New Block: {msg["result"]["data"]["value"]["block"]["header"]["height"]}"""
    )
    # reset redis things here


def on_error(ws, error):
    print("error", error)


def on_close(ws, close_status_code, close_msg):
    print("### closed ###")


def on_open(ws):
    print("Opened connection")
    ws.send(SUBSCRIBE_MSG)
    print("Sent subscribe request")


# from websocket import create_connection
if __name__ == "__main__":
    websocket.enableTrace(False)  # toggle to show or hide output
    ws = websocket.WebSocketApp(
        f"{RPC_WEBSOCKET}",
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
    )

    ws.run_forever(
        dispatcher=rel, reconnect=5
    )  # Set dispatcher to automatic reconnection, 5 second reconnect delay if connection closed unexpectedly
    rel.signal(2, rel.abort)  # Keyboard Interrupt
    rel.dispatch()
