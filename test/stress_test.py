import asyncio
import random
import string
import time
from aiohttp import ClientSession

fault = 0


async def signup_hacker(session):
    #url = "http://localhost:8000/hacker/signup"
    url = "https://backend.integration.lleidahack.dev/hacker/signup"
    hacker = {
        "nickname":
        ''.join(random.choices(string.ascii_uppercase + string.digits, k=10)),
        "name":
        "string",
        "password":
        ''.join(random.choices(string.ascii_uppercase + string.digits, k=10)),
        "email":
        ''.join(random.choices(string.ascii_uppercase + string.digits, k=10)) +
        "@gmail.com",
        "password":
        "String1234",
        "birthdate":
        "2023-10-02",
        "food_restrictions":
        "string",
        "telephone":
        ''.join(random.choices(string.digits, k=9)),
        "address":
        "string",
        "shirt_size":
        "S",
        "image":
        "",
        "is_image_url":
        True,
        "github":
        "string",
        "linkedin":
        "string"
    }
    #print(hacker['email'])
    async with session.post(url, json=hacker) as response:
        #assert response.status == 200, "Request failed"
        return await response.read()


async def main():
    async with ClientSession() as session:
        tasks = [signup_hacker(session) for _ in range(100)]
        responses = await asyncio.gather(*tasks)
        global fault
        for response in responses:
            print(response)
            if response == b'<html>\r\n<head><title>502 Bad Gateway</title></head>\r\n<body>\r\n<center><h1>502 Bad Gateway</h1></center>\r\n<hr><center>nginx/1.18.0 (Ubuntu)</center>\r\n</body>\r\n</html>\r\n':
                fault += 1


start_time = time.time()
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()
print("Execution time: %s seconds" % (time.time() - start_time))
print(fault)
