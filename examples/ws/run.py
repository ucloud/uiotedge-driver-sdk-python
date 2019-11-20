from uiotedgedriverlinksdk.edge import set_on_topo_change_callback, add_topo, delete_topo, get_topo, set_on_status_change_callback
from uiotedgedriverlinksdk.thing_client import ThingAccessClient
from uiotedgedriverlinksdk.thing_exception import UIoTEdgeDriverException, UIoTEdgeTimeoutException, UIoTEdgeDeviceOfflineException
import asyncio
import websockets
import json


async def handler(websocket, path):
    try:
        login = await websocket.recv()
        data = json.loads(login)

        if 'productSN' not in data or 'deviceSN' not in data:
            await websocket.send('please login first')
            await websocket.close()
            return

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

        client = ThingAccessClient(productSN, deviceSN,
                                   on_msg_callback=on_msg_callback)
        client.login()
        await websocket.send("login success")

        async for message in websocket:
            try:
                data = json.loads(message)
                print("receive subdev data: ", data)
                if 'action' in data:
                    action = data['action']
                    if action == 'add_topo':
                        add_topo(client.product_sn, client.device_sn)
                    elif action == 'delete_topo':
                        delete_topo(client.product_sn, client.device_sn)
                    elif action == "logout":
                        client.logout()
                        return
                    elif action == 'get_topo':
                        get_topo()
                elif 'topic' in data and 'payload' in data:
                    payload = data['payload']
                    if isinstance(payload, dict):
                        byts = json.dumps(payload)
                        client.publish(
                            topic=data['topic'], payload=byts.encode('utf-8'), is_cached=True, duration=30)
                    elif isinstance(payload, str):
                        byts = payload.encode('utf-8')
                        client.publish(
                            topic=data['topic'], payload=byts, is_cached=True, duration=30)

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
set_on_status_change_callback(lambda x: print('status change:', x))

# start websocket server
start_server = websockets.serve(handler, "0.0.0.0", 5678)
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
