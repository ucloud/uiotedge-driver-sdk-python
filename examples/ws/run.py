from uiotedgethingsdk.thing_client import ThingClient, set_on_topo_change_callback, get_topo
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

        queue = asyncio.Queue()

        def on_topo_add_callback(msg):
            print('topo add:', msg)
            queue.put(msg)
            # websocket.send(msg)

        client = ThingClient(productSN, deviceSN,
                             on_msg_callback=lambda x: print('msg:', x),
                             on_topo_add_callback=on_topo_add_callback,
                             on_topo_delete_callback=lambda x: print('topo delete:', x))
        client.login()

        async for message in websocket:
            try:
                data = json.loads(message)
                print("receive subdev data: ", data)
                if 'action' in data:
                    action = data['action']
                    if action == 'add_topo':
                        client.add_topo()
                    elif action == 'delete_topo':
                        client.delete_topo()
                    elif action == "logout":
                        client.logout()
                        return
                    elif action == "register":
                        client.register('12345678')
                    elif action == 'get_topo':
                        get_topo()
                elif 'topic' in data and 'payload' in data:
                    client.publish(data['topic'], data['payload'])
                else:
                    print('unknown message')
                    continue

            except Exception as e:
                print('read message error', e)
                continue

        async def wait():
            msg = await queue.get()
            await websocket.send(msg)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(wait)
        loop.close()

    except Exception as e:
        print('websocket error', e)
    finally:
        client.logout()
        print('connect closed .', deviceSN)

# set on topo change callback
set_on_topo_change_callback(lambda x: print('topo get or notify:', x))

# start websocket server
start_server = websockets.serve(handler, "0.0.0.0", 5678)
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
