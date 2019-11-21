from uiotedgedriverlinksdk.edge import set_on_topo_change_callback, add_topo, delete_topo, get_topo, set_on_status_change_callback, register_device
from uiotedgedriverlinksdk.client import ThingAccessClient
from uiotedgedriverlinksdk.exception import EdgeLinkDriverException, EdgeLinkDriverTimeoutException, EdgeLinkDriverDeviceOfflineException, EdgeLinkDriverOfflineException
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

        client = ThingAccessClient(product_sn, device_sn,
                                   on_msg_callback=on_msg_callback)

        print('start register ', product_sn, device_sn)
        register_device(product_sn, device_sn, secret)
        print('register success')

        print('start add topo success')
        add_topo(product_sn, device_sn)
        print('add topo success')

        print('start login')
        # client = ThingAccessClient(product_sn, device_sn,
        #                            on_msg_callback=on_msg_callback)
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
                            topic=data['topic'], payload=byts.encode('utf-8'))
                    elif isinstance(payload, str):
                        byts = payload.encode('utf-8')
                        client.publish(topic=data['topic'], payload=byts)

                else:
                    print('unknown message')
                    continue
            except EdgeLinkDriverDeviceOfflineException as e:
                await websocket.send("login message must be first")
            except EdgeLinkDriverTimeoutException as e:
                await websocket.send("wait response timeout")
            except EdgeLinkDriverOfflineException as e:
                await websocket.send('edge is offline, cannot send message to cloud')
            except EdgeLinkDriverException as e:
                await websocket.send(e.msg)
            except Exception as e:
                print('read message error', e)
    except EdgeLinkDriverException as e:
        await websocket.send(e)
    except Exception as e:
        print('websocket error', e)

# set on topo change callback
set_on_topo_change_callback(lambda x: print('topo get or notify:', x))
set_on_status_change_callback(lambda x: print('status change:', x))

# start websocket server
start_server = websockets.serve(handler, "0.0.0.0", 5678)
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
