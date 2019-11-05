from uiotedgethingsdk.thing_client import ThingClient, set_on_topo_change_callback
import asyncio
import websockets
import json


async def handler(websocket, path):
    try:
        login = await websocket.recv()
        data = json.loads(login)
        productSN = data['productSN']
        deviceSN = data['deviceSN']

        print('receive connect ', productSN, deviceSN)

        client = ThingClient(productSN, deviceSN, lambda x: x)
        client.login()
        # client.add_topo()

        async for message in websocket:
            try:
                data = json.loads(message)
                print("receive data: ", data)
                client.publish(data['topic'], data['payload'])
            except Exception as e:
                print('read message error', e)
                continue

    except Exception as e:
        print('websocket error', e)
    finally:
        client.logout()
        print('connect closed .', deviceSN)

# set on topo change callback
set_on_topo_change_callback(lambda x: print(x))

# start websocket server
start_server = websockets.serve(handler, "0.0.0.0", 5678)
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
