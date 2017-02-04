import asyncio
import time

async def funcA():
    print("funcA start")
    for i in range(0,10):
        print("funcA")
        await asyncio.sleep(0.2)

async def funcB():
    print("funcB start")
    for i in range(0,10):
        print("funcA")
        await asyncio.sleep(0.4)


def main():
    loop = asyncio.get_event_loop()
    #loop.run_until_complete(funcA())
    loop.call_soon_threadsafe(funcB())
    #loop.close()
    print("main wait")
    time.sleep(1)

if __name__ == '__main__':
    main()
