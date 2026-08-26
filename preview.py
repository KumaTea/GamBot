"""
A user account that hands the bot the picture behind a link.

Telegram renders link previews for people, not for bots. A bot is given
`webPageEmpty` for every page link it receives, and both of the methods
that would resolve one -- `messages.getWebPagePreview` and
`messages.getWebPage` -- answer a bot with `BOT_METHOD_INVALID`. A user
session has none of those limits: the preview arrives on the message
itself, with a full-size photo on it.

So the bot sends the link here and gets that photo straight back, as an
ordinary reply it can store and re-send like any other picture.

That is the whole program. Anything that is not a private message from
the bot is ignored -- there is deliberately nothing else to trigger.

Run it beside the bot, as its own process:

    python preview.py

The first run asks for the phone number and login code of the account
it should be, and writes the session next to this file.
"""

import asyncio
import logging
import configparser

from telethon import TelegramClient, events
from telethon.tl.types import (
    Document, DocumentAttributeAnimated, DocumentAttributeImageSize,
    MessageEntityTextUrl, MessageEntityUrl, MessageMediaWebPage,
    Photo, WebPage, WebPagePending
)


logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(funcName)12.12s> %(message)s',
    level=logging.INFO,
    datefmt='%m-%d %H:%M:%S')

config = configparser.ConfigParser()
config.read('config.ini')
# `[preview]` when it is there, `[jd]` otherwise -- one api_id serves a
# user session as well as it serves the bot, so there is nothing to add
# unless the session or the bot id needs to differ.
conf = config['preview'] if config.has_section('preview') else config['jd']

API_ID = int(conf['api_id'])
API_HASH = conf['api_hash']
SESSION = conf.get('session', 'preview')
BOT_ID = int(conf.get('bot_id', 6145808069))   # common.info.self_id

# Telegram goes and fetches the page *after* the message is delivered,
# so the first look at a fresh link is usually `webPagePending`. Re-read
# the message until the real page turns up, then give up.
TRIES = 6
WAIT = 1.5

client = TelegramClient(SESSION, API_ID, API_HASH)


def is_image_document(document: Document) -> bool:
    """A preview that came as a gif or an animation is a picture too."""
    if (document.mime_type or '').lower().startswith('image/'):
        return True
    return any(
        isinstance(a, (DocumentAttributeImageSize, DocumentAttributeAnimated))
        for a in (document.attributes or ())
    )


def has_link(message) -> bool:
    """
    Whether there is a url in the message at all.

    The bot answers in this chat -- it says what it did with the picture
    it was sent -- and those answers have no link and never grow one.
    Without this, each of them would be waited on for the full `TRIES`
    before being given up on.
    """
    return any(
        isinstance(e, (MessageEntityUrl, MessageEntityTextUrl))
        for e in (message.entities or ())
    )


def preview_image(message):
    """The picture on a message's link preview, if it has one yet."""
    media = getattr(message, 'media', None)
    if not isinstance(media, MessageMediaWebPage):
        return None

    page = media.webpage
    if not isinstance(page, WebPage):
        return None  # pending, empty, or no page behind the link at all
    if isinstance(page.photo, Photo):
        return page.photo
    if isinstance(page.document, Document) and is_image_document(page.document):
        return page.document
    return None


def still_coming(message) -> bool:
    """
    Whether Telegram might still attach a preview to this message.

    No media yet counts: a link that is being fetched can arrive with
    nothing on it and grow a preview a moment later. A link with no
    preview to give looks exactly the same, which is why this waits a
    bounded number of times rather than until something shows up.
    """
    media = getattr(message, 'media', None)
    if media is None:
        return True
    return isinstance(media, MessageMediaWebPage) and isinstance(
        media.webpage, WebPagePending)


async def resolve(message):
    """The preview picture, waiting out a page that is still pending."""
    picture = preview_image(message)
    for _ in range(TRIES):
        if picture is not None or not still_coming(message):
            break
        await asyncio.sleep(WAIT)
        message = await client.get_messages(BOT_ID, ids=message.id)
        if message is None:
            return None
        picture = preview_image(message)
    return picture


@client.on(events.NewMessage(chats=BOT_ID, from_users=BOT_ID, incoming=True))
async def hand_back(event):
    # `chats` already pins this to the private chat with the bot -- a
    # group the two of us share is a different chat_id and never gets
    # here. Saying so out loud costs nothing, and the one rule of this
    # program should be impossible to miss.
    if not event.is_private or not has_link(event.message):
        return

    try:
        picture = await resolve(event.message)
    except Exception as e:
        logging.warning(f'[preview]\tCould not read the preview of {event.id}: {e}')
        return

    if picture is None:
        logging.info(f'[preview]\tNothing to send back for {event.id}')
        return

    # a reply, so the bot knows which link it is getting an answer to
    await event.reply(file=picture)


async def main():
    await client.start()
    me = await client.get_me()
    logging.info(f'[preview]\tRunning as {me.id}, listening to {BOT_ID}')
    await client.run_until_disconnected()


if __name__ == '__main__':
    asyncio.run(main())
