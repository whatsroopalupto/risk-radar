"""Bounded AIS protocol diagnostic. Never prints credentials or raw frames."""
import asyncio
import json
from websockets.asyncio.client import connect
from backend.app.config import settings
from backend.app.connectors.ais import CORRIDORS, STREAM_URL, parse_position
from backend.app.db import utcnow

async def main():
    if not settings.aisstream_api_key:
        raise SystemExit("AIS key missing")
    async with connect(STREAM_URL, compression="deflate", open_timeout=15) as socket:
        await socket.send(json.dumps({"APIKey":settings.aisstream_api_key,
            "BoundingBoxes":list(CORRIDORS.values()), "FilterMessageTypes":["PositionReport"]}))
        deadline=asyncio.get_running_loop().time()+40
        positions=0
        while asyncio.get_running_loop().time()<deadline and positions<3:
            try:
                raw=await asyncio.wait_for(socket.recv(),timeout=max(0.1,deadline-asyncio.get_running_loop().time()))
            except asyncio.TimeoutError:
                print("No further messages within diagnostic window",flush=True)
                return
            message=json.loads(raw)
            kind=message.get("MessageType","provider_notice")
            print("Message type:",kind,flush=True)
            if kind=="PositionReport":
                positions+=1
                meta=message.get("MetaData",{})
                print("Metadata fields:",sorted(meta),flush=True)
                print("Timestamp:",meta.get("time_utc"),flush=True)
                print("Accepted by parser:",parse_position(message,utcnow()) is not None,flush=True)
            elif message.get("error") or message.get("Error"):
                print("Provider error (details withheld)",flush=True)
                return

if __name__=="__main__":
    asyncio.run(main())
