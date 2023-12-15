import asyncio
from propic.query import send_chat_member_photos
from propic.session import arg_parser, StatHolder, me


holder = StatHolder('propic/run.lock')


async def main(chat_id: int):
    async with me:
        await send_chat_member_photos(chat_id)

if __name__ == '__main__':
    args = arg_parser.parse_args()
    input_chat_id = int(args.chat_id)
    with holder:
        asyncio.run(main(input_chat_id))
