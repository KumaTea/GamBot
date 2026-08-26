import logging
from typing import Optional
from share.auth import ensure_auth
from share.common import is_command
from telethon.tl.custom import Message
from bot.media import message_image
from collect.store import collect_store
from collect.main import (
    Fleeting, Quiet, archive_message, carries_picture, fade,
    recent_messages, send_item
)
from collect.config import (
    ARCHIVISTS, COLLECTIONS, Collection, DEFAULT_COLLECTION, collection_of_keyword
)


def may_archive(user_id: int) -> bool:
    return user_id in ARCHIVISTS


async def source_message(event) -> Optional[Message]:
    """
    The message whose picture a keyword refers to.

    Its own, if it has one; otherwise whatever it quotes; otherwise the
    last thing the same person said that had a picture or a link in it.
    That ordering is what makes "send a picture captioned ruby", "reply
    ruby to one", and "say ruby just after one" all work.
    """
    message = event.message
    if carries_picture(message):
        return message

    replied = await event.get_reply_message()
    if replied is not None and carries_picture(replied):
        return replied

    return recent_messages.before(event.chat_id, event.sender_id)


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

    report = await archive_message(collection, replied, added_by=event.sender_id)
    if not report:
        return None

    recent_messages.forget(event.chat_id, event.sender_id, replied.id)
    return await say(event, report)


async def archive_for(event, collections: list[Collection]) -> Optional[Message]:
    source = await source_message(event)
    if source is None:
        return None

    lines = []
    for collection in collections:
        report = await archive_message(collection, source, added_by=event.sender_id)
        if report:
            lines.append(report)
    if not lines:
        return None

    recent_messages.forget(event.chat_id, event.sender_id, source.id)
    # nobody asked, so only an answer worth volunteering gets made: this
    # is the one path a keyword reaches on its own, and "ruby" lands in
    # ordinary sentences too
    return await say(event, *(line for line in lines if not isinstance(line, Quiet)))


async def watch_messages(event) -> Optional[Message]:
    """
    Watch a chat go by, filing pictures when told to.

    Deliberately not behind `ensure_auth`: it has to see the messages an
    archivist sends to know which picture "ruby" is pointing at, and
    the only thing it ever acts on is a keyword from one.
    """
    message = event.message
    text = message.raw_text or ''

    if not may_archive(event.sender_id):
        return None

    # `/ruby` is a request for a picture, not an instruction to file one
    if is_command(text):
        return None

    collections = collection_of_keyword(text)
    if collections:
        return await archive_for(event, collections)

    # not a keyword, so it is a candidate for the next one to point back
    # at. Remembered after that check and never before: a keyword put in
    # the queue would push the very picture it refers to out of it.
    recent_messages.remember(event.chat_id, event.sender_id, message)
    return None


async def archive_private(event) -> Optional[Message]:
    """
    A picture or a link sent straight to the bot gets filed.

    No keyword needed here -- there is nothing else a picture in the
    bot's own chat could mean.
    """
    if not may_archive(event.sender_id):
        return None

    message = event.message
    text = message.raw_text or ''
    named = collection_of_keyword(text)
    collections = named or [COLLECTIONS[DEFAULT_COLLECTION]]

    if not carries_picture(message):
        return None

    lines = []
    for collection in collections:
        report = await archive_message(collection, message, added_by=event.sender_id)
        if report:
            lines.append(report)
    return await say(event, *lines)


async def archive_preview(event) -> Optional[Message]:
    """
    File a picture the preview account sent back.

    `hand_to_preview` gave that account a link and stopped; this is the
    far end of it. The picture turns up on its own some seconds later
    and is filed then, so nothing had to be kept waiting -- which is
    also why there is no request here to match it against.

    That is what pins it to one collection: the picture answers a link,
    not a `/ruby`, and a link says nothing about which pile it was meant
    for. Adding a second pile would mean saying so in the message.
    """
    if message_image(event.message) is None:
        return None

    collection = COLLECTIONS[DEFAULT_COLLECTION]
    report = await archive_message(collection, event.message, added_by=event.sender_id)
    return await event.reply(report) if report else None


def make_command(collection: Collection):
    """One `/name` handler, bound to one collection."""

    @ensure_auth
    async def command(event) -> Optional[Message]:
        # an archivist pointing the command at a picture is filing it,
        # not asking for one; everyone else always gets a picture
        if may_archive(event.sender_id):
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
