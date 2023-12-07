import os
import pickle
from common.data import USER_PHOTO_DIR, USER_PHOTO_FILE


class UserPhotoStore:
    def __init__(self):
        self.photos = {}
        self.groups = []
        self.load()

    def save(self, user_id: int, file_id: str, dump: bool = False):
        self.photos[user_id] = file_id
        if dump:
            self.dump()

    def get(self, user_id: int) -> str:
        return self.photos.get(user_id)

    def load(self):
        if os.path.isfile(f'{USER_PHOTO_DIR}/{USER_PHOTO_FILE}'):
            with open(f'{USER_PHOTO_DIR}/{USER_PHOTO_FILE}', 'rb') as f:
                data = pickle.load(f)
                self.photos = data['photos']
                self.groups = data['groups']

    def dump(self):
        with open(f'{USER_PHOTO_DIR}/{USER_PHOTO_FILE}', 'wb') as f:
            data = {
                'photos': self.photos,
                'groups': self.groups
                }
            pickle.dump(data, f)

    def update(self, user_id: int, file_id: str):
        return self.save(user_id, file_id)

    def register_group(self, chat_id: int):
        if chat_id not in self.groups:
            self.groups.append(chat_id)
            self.dump()

    def unregister_group(self, chat_id: int):
        if chat_id in self.groups:
            self.groups.remove(chat_id)
            self.dump()


user_photos = UserPhotoStore()
