from uiotedgethingsdk.thing_client import ThingClient, set_on_topo_change_callback, get_topo
from uiotedgethingsdk.thing_exception import UIoTEdgeDriverException, UIoTEdgeTimeoutException, UIoTEdgeDeviceOfflineException
import asyncio
import websockets
import json


async def handler(websocket, path):
    try:
        login = await websocket.recv()
        data = json.loads(login)
        productSN = data['productSN']
        deviceSN = data['deviceSN']

        if 'productSN' not in data or 'deviceSN' not in data:
            await websocket.send('please login first')
            await websocket.close()
            return

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
        client.login()
        await websocket.send("login success")

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
    except UIoTEdgeDeviceOfflineException as e:
        await websocket.send("login message must be first")
    except UIoTEdgeDriverException as e:
        await websocket.send(e.msg)
    except UIoTEdgeTimeoutException as e:
        await websocket.send('login timeout')
    except Exception as e:
        print('websocket error', e)
    finally:
        client.logout()
        await websocket.close()
        print('connect closed .', deviceSN)

# set on topo change callback
set_on_topo_change_callback(lambda x: print('topo get or notify:', x))

# start websocket server
start_server = websockets.serve(handler, "0.0.0.0", 5678)
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
