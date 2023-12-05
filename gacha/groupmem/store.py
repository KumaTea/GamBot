import os
import pickle
from common.data import USER_PHOTO_DIR, USER_PHOTO_FILE


class UserPhotoStore:
    def __init__(self):
        self.photos = {}
        self.load()

    def save(self, user_id: int, file_id: str):
        self.photos[user_id] = file_id
        self.dump()

    def get(self, user_id: int) -> str:
        return self.photos.get(user_id)

    def load(self):
        if os.path.isfile(f'{USER_PHOTO_DIR}/{USER_PHOTO_FILE}'):
            with open(f'{USER_PHOTO_DIR}/{USER_PHOTO_FILE}', 'rb') as f:
                self.photos = pickle.load(f)

    def dump(self):
        with open(f'{USER_PHOTO_DIR}/{USER_PHOTO_FILE}', 'wb') as f:
            pickle.dump(self.photos, f)

    def update(self, user_id: int, file_id: str):
        return self.save(user_id, file_id)


user_photos = UserPhotoStore()
