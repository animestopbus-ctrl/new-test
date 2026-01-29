import motor.motor_asyncio
import datetime
from config import DB_NAME, DB_URI
from logger import LOGGER

logger = LOGGER(__name__)

class Database:
    
    def __init__(self, uri, database_name):
        self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.col = self.db.users

    def new_user(self, id, name):
        return dict(
            id = id,
            name = name,
            session = None,
            daily_usage = 0,
            limit_reset_time = None,
            total_saves = 0,
            is_premium = False,
            premium_expiry = None,
            delete_words = [],
            replace_words = {},
            caption = None,
            thumbnail = None,
            dump_chat = None,
            banned = False
        )
    
    async def add_user(self, id, name):
        user = self.new_user(id, name)
        await self.col.insert_one(user)
        logger.info(f"New user added to DB: {id} - {name}")
    
    async def is_user_exist(self, id):
        user = await self.col.find_one({'id':int(id)})
        return bool(user)
    
    async def total_users_count(self):
        count = await self.col.count_documents({})
        return count

    async def get_all_users(self):
        return self.col.find({})

    async def delete_user(self, user_id):
        await self.col.delete_many({'id': int(user_id)})
        logger.info(f"User deleted from DB: {user_id}")

    async def set_session(self, id, session):
        await self.col.update_one({'id': int(id)}, {'$set': {'session': session}})

    async def get_session(self, id):
        user = await self.col.find_one({'id': int(id)})
        return user.get('session')

    async def set_caption(self, id, caption):
        await self.col.update_one({'id': int(id)}, {'$set': {'caption': caption}})

    async def get_caption(self, id):
        user = await self.col.find_one({'id': int(id)})
        return user.get('caption', None)

    async def del_caption(self, id):
        await self.col.update_one({'id': int(id)}, {'$unset': {'caption': ""}})

    async def set_thumbnail(self, id, thumbnail):
        await self.col.update_one({'id': int(id)}, {'$set': {'thumbnail': thumbnail}})

    async def get_thumbnail(self, id):
        user = await self.col.find_one({'id': int(id)})
        return user.get('thumbnail', None)

    async def del_thumbnail(self, id):
        await self.col.update_one({'id': int(id)}, {'$unset': {'thumbnail': ""}})

    async def set_dump_chat(self, id, chat_id):
        await self.col.update_one({'id': int(id)}, {'$set': {'dump_chat': chat_id}})

    async def get_dump_chat(self, id):
        user = await self.col.find_one({'id': int(id)})
        return user.get('dump_chat', None)

    async def del_dump_chat(self, id):
        await self.col.update_one({'id': int(id)}, {'$unset': {'dump_chat': ""}})

    async def ban_user(self, id):
        await self.col.update_one({'id': int(id)}, {'$set': {'banned': True}})

    async def unban_user(self, id):
        await self.col.update_one({'id': int(id)}, {'$set': {'banned': False}})

    async def is_banned(self, id):
        user = await self.col.find_one({'id': int(id)})
        return user.get('banned', False)

    async def set_delete_words(self, id, words):
        current_del = await self.get_delete_words(id) or []
        new_del = list(set(current_del + words))
        await self.col.update_one({'id': int(id)}, {'$set': {'delete_words': new_del}})

    async def get_delete_words(self, id):
        user = await self.col.find_one({'id': int(id)})
        return user.get('delete_words', [])

    async def remove_delete_words(self, id, words):
        current_del = await self.get_delete_words(id) or []
        new_del = [w for w in current_del if w not in words]
        await self.col.update_one({'id': int(id)}, {'$set': {'delete_words': new_del}})

    async def set_replace_words(self, id, repl_dict):
        current_repl = await self.get_replace_words(id) or {}
        current_repl.update(repl_dict)
        await self.col.update_one({'id': int(id)}, {'$set': {'replace_words': current_repl}})

    async def get_replace_words(self, id):
        user = await self.col.find_one({'id': int(id)})
        return user.get('replace_words', {})

    async def remove_replace_words(self, id, targets):
        current_repl = await self.get_replace_words(id) or {}
        for target in targets:
            current_repl.pop(target, None)
        await self.col.update_one({'id': int(id)}, {'$set': {'replace_words': current_repl}})

    async def check_limit(self, id):
        user = await self.col.find_one({'id': int(id)})
        if not user:
            return False
        
        if user.get('is_premium'):
            return False 

        now = datetime.datetime.now()
        reset_time = user.get('limit_reset_time')
        
        if reset_time is None or now >= reset_time:
            await self.col.update_one(
                {'id': int(id)}, 
                {'$set': {'daily_usage': 0, 'limit_reset_time': now + datetime.timedelta(hours=24)}}
            )
            return False

        usage = user.get('daily_usage', 0)
        if usage >= 10:
            return True 
        
        return False 

    async def add_traffic(self, id):
        user = await self.col.find_one({'id': int(id)})
        
        if user.get('is_premium'):
            await self.col.update_one({'id': int(id)}, {'$inc': {'total_saves': 1}})
            return

        now = datetime.datetime.now()
        reset_time = user.get('limit_reset_time')

        if reset_time is None or now >= reset_time:
            new_reset_time = now + datetime.timedelta(hours=24)
            await self.col.update_one(
                {'id': int(id)}, 
                {'$set': {'daily_usage': 1, 'limit_reset_time': new_reset_time}}
            )
        else:
            await self.col.update_one(
                {'id': int(id)}, 
                {'$inc': {'daily_usage': 1}}
            )
        
        await self.col.update_one({'id': int(id)}, {'$inc': {'total_saves': 1}})

    async def add_premium(self, id, expiry):
        await self.col.update_one({'id': int(id)}, {'$set': {'is_premium': True, 'premium_expiry': expiry}})

    async def remove_premium(self, id):
        await self.col.update_one({'id': int(id)}, {'$set': {'is_premium': False, 'premium_expiry': None}})

    async def check_premium(self, id):
        user = await self.col.find_one({'id': int(id)})
        is_prem = user.get('is_premium', False)
        expiry = user.get('premium_expiry')
        if expiry and datetime.datetime.fromisoformat(expiry) < datetime.datetime.now():
            await self.remove_premium(id)
            return False
        return is_prem

db = Database(DB_URI, DB_NAME)
