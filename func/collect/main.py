import logging
from typing import Optional
from share.auth import ensure_auth
from share.common import get_command_args
from telethon.tl.custom import Message
from bot.media import as_ref, message_image
from collect.store import collect_store
from collect.main import (
    Fleeting, archive_message, carries_picture, fade, send_item, waiting
)
from collect.config import (
    ARCHIVISTS, COLLECTIONS, DELETE_WORDS, NO_ARCHIVE,
    Collection, DEFAULT_COLLECTION
)


def may_archive(user_id: int) -> bool:
    return user_id in ARCHIVISTS


async def say(event, *lines: str) -> Optional[Message]:
    """
    Reply with a report, and take back the parts that do not keep.

    Everything filed says so permanently. A link handed to the preview
    account is the one thing that does not: it is news for a minute,
    and the picture it promises reports itself when it lands.
    """
    said = [line for line in lines if line]
    if not said:
        return None

    sent = await event.reply('\n'.join(said))
    if any(isinstance(line, Fleeting) for line in said):
        fade(sent)
    return sent


async def archive_reply(event, collection: Collection) -> Optional[Message]:
    """
    File the picture a `/ruby` was aimed at, if it was aimed at one.

    Returns None whenever there is nothing to file -- no reply, or a
    reply to something without a picture in it -- which is the caller's
    signal to go back to handing a picture out instead.
    """
    replied = await event.get_reply_message()
    if replied is None or not carries_picture(replied):
        return None

    report = await archive_message(
        collection, replied, added_by=event.sender_id, asked_by=event.message)
    if not report:
        return None
    return await say(event, report)


async def archive_private(event) -> Optional[Message]:
    """
    A picture or a link sent straight to the bot gets filed.

    No command needed here -- there is nothing else a picture in the
    bot's own chat could mean, short of `#NoArchive` saying so.
    """
    if not may_archive(event.sender_id):
        return None

    message = event.message
    if NO_ARCHIVE in (message.raw_text or '').lower():
        return None
    if not carries_picture(message):
        return None

    report = await archive_message(
        COLLECTIONS[DEFAULT_COLLECTION], message,
        added_by=event.sender_id, asked_by=message)
    return await say(event, report)


async def archive_preview(event) -> Optional[Message]:
    """
    File a picture the preview account sent back.

    `hand_to_preview` gave that account a link and stopped; this is the
    far end of it. The picture is a reply to that link, which is what
    finds the request it answers -- and the picture is shown there,
    under the request, with the id it was filed as. That is the moment
    to see that a page's preview was the wrong picture, and to answer it
    with `/ruby delete`.

    The pile is always the default one: a link says nothing about which
    pile it was meant for. Adding a second pile would mean remembering
    that alongside the request.
    """
    picture = message_image(event.message)
    if picture is None:
        return None

    collection = COLLECTIONS[DEFAULT_COLLECTION]
    report = await archive_message(collection, event.message, added_by=event.sender_id)
    if not report:
        return None

    asked = waiting.pop(event.message.reply_to_msg_id, None)
    if asked is not None:
        chat_id, msg_id = asked
        try:
            return await event.client.send_file(
                chat_id, picture, caption=report, reply_to=msg_id)
        except Exception as e:
            logging.warning(f'[collect]\tCould not show the picture in {chat_id}: {e}')
    return await event.reply(report)


# -- `/ruby <word>`, for an archivist


async def named_item(event, collection: Collection, target: Optional[str]):
    """
    The stored picture a `/ruby delete` means.

    By id or by url when one is given -- the id is the `#` number every
    filing report carries -- and otherwise whatever picture the command
    was replied to, found by the media Telegram already holds. That last
    one is the useful gesture: the bot hands a picture out, it turns out
    to be the wrong one, you reply to it.
    """
    if target:
        target = target.lstrip('#')
        if target.isdigit():
            item = collect_store.get(int(target))
            return item if item and item.collection == collection.name else None
        return collect_store.by_url(collection.name, target)

    replied = await event.get_reply_message()
    picture = message_image(replied) if replied else None
    ref = as_ref(picture) if picture is not None else None
    return collect_store.by_media(collection.name, ref.id) if ref else None


async def delete_item(event, collection: Collection, args: list[str]) -> Message:
    """Take one picture back out of a collection."""
    item = await named_item(event, collection, args[1] if len(args) > 1 else None)
    if item is None:
        return await say(event, f'{collection.label}：没找到要删的那张。')

    collect_store.remove(item.id)
    return await say(
        event, f'{collection.label} -1（#{item.id}，还剩 {collect_store.count(collection.name)} 张）')


async def show_item(event, collection: Collection, target: str) -> Message:
    """
    `/ruby 42`: one picture by id, captioned with it.

    The database cannot show what a row looks like -- its picture is a
    Telegram file reference -- so this is how a row is looked at before
    deciding to delete it.
    """
    item = collect_store.get(int(target.lstrip('#')))
    if item is None or item.collection != collection.name:
        return await say(event, f'{collection.label}：没有 #{target.lstrip("#")} 这张。')

    sent = await send_item(event, item, caption=f'#{item.id}')
    return sent or await say(event, f'{collection.label}：#{item.id} 拿不出来了。')


async def subcommand(event, collection: Collection, args: list[str]) -> Optional[Message]:
    """`/ruby delete` and `/ruby <id>`, or None for anything else."""
    word = args[0].lower()
    if word in DELETE_WORDS:
        return await delete_item(event, collection, args)
    if word.lstrip('#').isdigit():
        return await show_item(event, collection, word)
    return None


def make_command(collection: Collection):
    """One `/name` handler, bound to one collection."""

    @ensure_auth
    async def command(event) -> Optional[Message]:
        # an archivist pointing the command at a picture is filing it,
        # not asking for one; everyone else always gets a picture
        if may_archive(event.sender_id):
            args = get_command_args(event.raw_text)
            if args:
                handled = await subcommand(event, collection, args)
                if handled:
                    return handled

            filed = await archive_reply(event, collection)
            if filed:
                return filed

        total = collect_store.count(collection.name)
        if not total:
            return await event.respond(collection.empty_text)

        item = collect_store.random(collection.name)
        sent = await send_item(event, item)
        if sent:
            return sent

        logging.warning(f'[collect]\t{collection.name}: item {item.id} failed, trying another')
        another = collect_store.random(collection.name, exclude=item.id)
        if another:
            sent = await send_item(event, another)
            if sent:
                return sent
        return await event.respond(f'{collection.label}：图片拿不出来了。')

    command.__name__ = f'command_{collection.name}'
    return command


collection_commands = {name: make_command(c) for name, c in COLLECTIONS.items()}
