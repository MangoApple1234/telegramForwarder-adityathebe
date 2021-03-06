import logging
import telethon
import hypercorn.asyncio
from quart import Quart, request, Blueprint
from telethon import TelegramClient, events, sync
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.tl.functions.channels import JoinChannelRequest
from client import telegram_client
from config import API_PORT
from forwarder import forwarder_event_handler

print("API_PORT", API_PORT)
format_str = '[%(levelname)s] %(filename)s:%(lineno)s -- %(message)s'
logging.basicConfig(level=logging.INFO, format=format_str)


# Create Flask application instance
app = Quart(__name__)


@app.route('/')
def index():
    return "Telethon API is up and running"


@app.route('/joinPublicUserEntity')
async def joinPublicUserEntity():
    """
    Join Private Users
    """
    entity = request.args.get('entity')

    app.logger.info('[/joinPublicUserEntity] :: Entity Name {}'.format(entity))
    try:
        msg = '/start'
        result = await telegram_client.get_entity(entity)
        return result.to_dict()
    except Exception as exception:
        return {'error': str(exception)}


@app.route('/joinPublicEntity')
async def joinPublicEntity():
    """
    Join Public Groups & Channels
    """
    entity = request.args.get('entity')
    app.logger.info('[/joinPublicEntity] :: Entity Name {}'.format(entity))
    try:
        result = await telegram_client(JoinChannelRequest(entity))
        return result.chats[0].to_dict()
    except telethon.errors.rpcerrorlist.UserAlreadyParticipantError:
        return {'success': 'ok'}
    except Exception as exception:
        return {'error': str(exception)}


@app.route('/joinPrivateEntity')
async def joinPrivateEntity():
    """
    Join Invation Link
    """
    hash = request.args.get('hash')
    app.logger.info('[/joinPrivateEntity] :: Hash {}'.format(hash))
    try:
        result = await telegram_client(ImportChatInviteRequest(hash))
        return result.chats[0].to_dict()
    except telethon.errors.rpcerrorlist.UserAlreadyParticipantError:
        return {'succes': 'ok'}
    except Exception as exception:
        app.logger.error(exception)
        return {'error': str(exception)}


@app.route('/getentity', methods=['GET'])
async def getEntity():
    entity = request.args.get('entity')
    is_entity_id = request.args.get('is_id') or '0'

    if (is_entity_id == '1'):
        entity = int(entity)

    app.logger.info('[/getentity] :: Entity Name {}'.format(entity))
    try:
        result = await telegram_client.get_entity(entity)
        return result.to_dict()
    except Exception as exception:
        app.logger.error(exception)
        return {'error': str(exception)}


@app.before_serving
async def startup():
    await telegram_client.start()
    user = await telegram_client.get_me()
    app.logger.info('Logged in as @{}'.format(user.username))


@app.after_serving
async def cleanup():
    await telegram_client.disconnect()


async def main():
    hypercorn_config = hypercorn.Config()
    hypercorn_config.bind = [f"0.0.0.0:{API_PORT}"]
    await hypercorn.asyncio.serve(app, hypercorn_config)


if __name__ == "__main__":
    telegram_client.on(events.NewMessage)(forwarder_event_handler)
    telegram_client.loop.run_until_complete(main())
