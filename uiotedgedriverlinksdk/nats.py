import asyncio
import json
import sys
from nats.aio.client import Client as NATS
from nats.aio.errors import ErrConnectionClosed, ErrTimeout, ErrNoServers

nc = NATS()

async def init_nats(loop, url, msg_handler, broadcast_msg_handler, driver_id):

    async def message_handler(msg):
        subject = msg.subject
        reply = msg.reply
        data = msg.data.decode()
        # print("Received a message on '{subject} {reply}': {data}".format(
            # subject=subject, reply=reply, data=data))
        msg_handler(data)
    
    async def broadcast_message_handler(msg):
        subject = msg.subject
        reply = msg.reply
        data = msg.data.decode()
        # print("Received a broadcast message on '{subject} {reply}': {data}".format(
            # subject=subject, reply=reply, data=data))
        broadcast_msg_handler(data)

    try:
        await nc.connect(servers=[url], loop=loop)
        print('connect success')
    except Exception as e:
        print(e)
        sys.exit(0)

    if nc.is_connected:
        await nc.subscribe("edge.local."+driver_id, cb=message_handler)
        # print('sub 1 success:', sid)
        await nc.subscribe("edge.local.broadcast", cb=broadcast_message_handler)
        # print('sub 2 success', sid)


async def init_nat_publish(q, driver_id):
    while True:
        msg = q.get()
        try:
            bty = json.dumps(msg)
            # print("send message")
            await nc.publish(subject='edge.router.'+driver_id,
                            payload=bty.encode('utf-8'))
            await nc.flush()
        except Exception as e:
            print(e)


# if __name__ == '__main__':
#     loop = asyncio.get_event_loop()
#     loop.run_until_complete(run(loop))
#     loop.close()


    
