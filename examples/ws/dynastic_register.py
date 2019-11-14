from uiotedgethingsdk.thing_client import ThingAccessClient, set_on_topo_change_callback, get_topo, set_on_status_change_callback, register_device
from uiotedgethingsdk.thing_exception import UIoTEdgeDriverException, UIoTEdgeTimeoutException, UIoTEdgeDeviceOfflineException
import asyncio
import websockets
import json


async def handler(websocket, path):
    try:
        login = await websocket.recv()
        data = json.loads(login)

        if 'productSN' not in data or 'deviceSN' not in data or 'secret' not in data:
            await websocket.send('please input productSN, deviceSN, secret ....')
            await websocket.close()
            return

        product_sn = data['productSN']
        device_sn = data['deviceSN']
        secret = data['secret']

        print('start register ', product_sn, device_sn)
        register_device(product_sn, device_sn, secret)

        print('register success')

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

        print('start login')
        client = ThingAccessClient(product_sn, device_sn,
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
                        client.add_topo()
                    elif action == 'delete_topo':
                        client.delete_topo()
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
                            topic=data['topic'], payload=byts.encode('utf-8'))
                    elif isinstance(payload, str):
                        byts = payload.encode('utf-8')
                        client.publish(topic=data['topic'], payload=byts)

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
