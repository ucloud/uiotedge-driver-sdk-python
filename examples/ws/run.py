from uiotedgethingsdk.thing_client import ThingClient, set_on_topo_change_callback, get_topo
from uiotedgethingsdk.thing_exception import UIoTEdgeDriverException, UIoTEdgeTimeoutException
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

        async def send_to_websocket(msg):
            await websocket.send(msg)

        def send(msg):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(send_to_websocket(str(msg)))
            loop.close()

        def on_msg_callback(msg):
            print('msg receive:', msg)
            send(msg)

        def on_status_change_callback(msg):
            print('status change:', msg)
            send(msg)

        client = ThingClient(productSN, deviceSN,
                             on_msg_callback=on_msg_callback,
                             on_disable_enable_callback=on_status_change_callback)
        try:
            client.login()
            await websocket.send("connect success")
        except UIoTEdgeDriverException as e:
            print('login failed:'+e.msg)
            await websocket.send(e.msg)
            await websocket.close()
            return
        except UIoTEdgeTimeoutException as e:
            print('login failed: timeout')
            await websocket.send('login timeout')
            await websocket.close()
            return
        except Exception as e:
            print(e)
            return

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

    except Exception as e:
        print('websocket error', e)
    finally:
        client.logout()
        websocket.close()
        print('connect closed .', deviceSN)
        return

# set on topo change callback
set_on_topo_change_callback(lambda x: print('topo get or notify:', x))

# start websocket server
start_server = websockets.serve(handler, "0.0.0.0", 5678)
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
