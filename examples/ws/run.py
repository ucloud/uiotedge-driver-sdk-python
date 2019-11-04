from uiotedgethingsdk.thing_client import ThingClient

import asyncio
import datetime
import random
import websockets
import json


async def handler(websocket, path):
    try:
        login = await websocket.recv()
        data = json.loads(login)
        deviceSN = data['deviceSN']

        print('receive connect ', deviceSN)

        client = ThingClient(deviceSN, "0001", lambda x: x)
        client.login()

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

start_server = websockets.serve(handler, "0.0.0.0", 5678)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
