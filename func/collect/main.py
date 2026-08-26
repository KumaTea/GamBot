import logging
from typing import Optional
from share.auth import ensure_auth
from share.common import is_command
from telethon.tl.custom import Message
from bot.media import message_image, webpage_url
from collect.store import collect_store
from collect.main import (
    archive_message, first_link, looks_like_image_url,
    recent_media, refetch, send_item
)
from collect.config import (
    ARCHIVISTS, COLLECTIONS, Collection, DEFAULT_COLLECTION, collection_of_keyword
)


def may_archive(user_id: int) -> bool:
    return user_id in ARCHIVISTS


def carries_picture(message: Message) -> bool:
    return message_image(message) is not None or bool(webpage_url(message) or first_link(message))


async def source_message(event) -> Optional[Message]:
    """
    The message whose picture a keyword refers to.

    Its own, if it has one; otherwise whatever it quotes; otherwise the
    last picture the chat saw. That ordering is what makes both "send a
    picture captioned ruby" and "say ruby right after one" work.
    """
    message = event.message
    if carries_picture(message):
        return message

    replied = await event.get_reply_message()
    if replied is not None and carries_picture(replied):
        return replied

    msg_id = recent_media.latest(event.chat_id)
    if msg_id:
        return await refetch(event.client, event.chat_id, msg_id)
    return None


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

    recent_media.forget(event.chat_id, replied.id)
    return await event.reply(report)


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

    recent_media.forget(event.chat_id, source.id)
    return await event.reply('\n'.join(lines))


async def watch_messages(event) -> Optional[Message]:
    """
    Watch a chat go by, filing pictures when told to.

    Deliberately not behind `ensure_auth`: it has to see every message
    to know which picture "ruby" is pointing at, and the only thing it
    acts on is a keyword from an archivist.
    """
    message = event.message
    # only remember what could actually be filed later -- a page link
    # can never be, and remembering one would shadow a real picture
    if message_image(message) is not None or looks_like_image_url(
            webpage_url(message) or first_link(message)):
        recent_media.remember(event.chat_id, message.id)

    text = message.raw_text or ''
    if not may_archive(event.sender_id):
        return None

    # `/ruby` is a request for a picture, not an instruction to file one
    if is_command(text):
        return None

    collections = collection_of_keyword(text)
    if collections:
        return await archive_for(event, collections)
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
    return await event.reply('\n'.join(lines)) if lines else None


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
