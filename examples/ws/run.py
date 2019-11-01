from uiotedgethingsdk.thing_client import ThingClient

import asyncio
import datetime
import random
import websockets
import json


async def handler(websocket, path):
    login = await websocket.recv()
    data = json.loads(login)
    deviceSN = data['deviceSN']

    print('receive connect ', deviceSN)

    client = ThingClient(deviceSN, "0001", lambda x: x)
    client.registerAndOnline()

    try:
        async for message in websocket:
            data = json.loads(message)
            client.publish(data['topic'], data['payload'])

    except Exception as e:
        print(e)
    finally:
        print('connect closed .', deviceSN)

start_server = websockets.serve(handler, "0.0.0.0", 5678)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
