from uiotedgedriverlinksdk.edge import set_on_topo_change_callback, add_topo, delete_topo, get_topo, set_on_status_change_callback, register_device
from uiotedgedriverlinksdk.client import ThingAccessClient, Config, getConfig
from uiotedgedriverlinksdk.exception import EdgeDriverLinkException, EdgeDriverLinkTimeoutException, EdgeDriverLinkDeviceOfflineException, EdgeDriverLinkOfflineException, BaseEdgeException
import asyncio
import websockets
import json
import urllib.parse as urlparse

# ws://127.0.0.1:8080/?product_sn=4clmd5fx58kp8lua&device_sn=1000101


async def handler(websocket, path):
    parsed = urlparse.urlparse(path)
    querys = urlparse.parse_qs(parsed.query)
    client = ThingAccessClient()
    try:
        product_sn = str(querys['product_sn'][0])
        device_sn = str(querys['device_sn'][0])

        print('receive connect ', product_sn, device_sn)

        print('readc config', getConfig())

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

        # client = ThingAccessClient(productSN, deviceSN,
        #                            on_msg_callback=on_msg_callback)
        client.set_product_sn(product_sn)
        client.set_device_sn(device_sn)
        client.set_msg_callback(on_msg_callback)

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
            except EdgeDriverLinkDeviceOfflineException as e:
                await websocket.send(str(e))
            except EdgeDriverLinkOfflineException as e:
                await websocket.send(str(e))
            except EdgeDriverLinkTimeoutException as e:
                await websocket.send(str(e))
            except EdgeDriverLinkException as e:
                await websocket.send(str(e))
            except Exception as e:
                print('read message error', e)
                continue

    except BaseEdgeException as e:
        await websocket.send(str(e))
    except Exception as e:
        print('websocket error', e)
    finally:
        client.logout()
        print('connect closed .', device_sn)


if __name__ == "__main__":
    # set on topo change callback
    # init_driver(asyncio.get_event_loop())
    set_on_topo_change_callback(lambda x: print('topo change notify:', x))
    set_on_status_change_callback(lambda x: print('status change:', x))

    # start websocket server
    start_server = websockets.serve(
        ws_handler=handler, host='0.0.0.0', port=5678)
    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()
