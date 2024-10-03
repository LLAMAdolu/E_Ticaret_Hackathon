from repositories import UserRepository, ProductRepository
from googletrans import Translator
from PIL import Image

class UserService:
    def __init__(self):
        self.user_repo = UserRepository()

    def check_login(self, username, password):
        """
        Check if the provided username and password are correct.

        :param username: The username entered by the user.
        :param password: The password entered by the user.
        :return: Tuple (True, user_id) if login is successful, else (False, None).
        """
        user = self.user_repo.get_user_by_username(username)
        if user:
            user_id, db_username, db_password = user

            # If passwords are stored in plain text (not recommended)
            if password == db_password:
                return True, user_id

        return False, None
    
    def username_exists(self, username):
        """
        Check if a username exists in the database.

        :param username: The username to check.
        :return: True if the username exists, False otherwise.
        """
        user = self.user_repo.get_user_by_username(username)
        return user is not None  # If a user is found, return True, else False

    def register_user(self, name, username, email, password, city=None, region=None):
        self.user_repo.create_user(name, username, email, password, city, region)

    def get_user_region(self, user_id):
        return self.user_repo.get_user_region(user_id)
        
    def get_user_details(self, user_id):
        return self.user_repo.get_user(user_id)

    def update_user_info(self, user_id, **kwargs):
        self.user_repo.update_user(user_id, **kwargs)

    def delete_user_account(self, user_id):
        self.user_repo.delete_user(user_id)


class ProductService:
    def __init__(self):
        self.product_repo = ProductRepository()
        self.translator = Translator()

    def add_product(self, user_id, header_text, image_path, description):
        self.product_repo.create_product(user_id, header_text, image_path, description)

    def get_product_info(self, product_id):
        return self.product_repo.get_product(product_id)

    def get_all_products_as_list(self):
        products = self.product_repo.get_all_products_as_list()
        # If additional processing is needed, you can add it here
        return products
    
    def get_all_products_as_english_list(self):
        products = self.product_repo.get_all_products_as_list()
        translated_products = []

        # Her ürünün 'name' ve 'description' alanlarını İngilizce'ye çevir, 'image' alanını çevirme
        for product in products:
            translated_name = self.translator.translate(product['name'], dest='en').text
            translated_description = self.translator.translate(product['description'], dest='en').text

            translated_product = {
                "user_id":product['user'],
                "name": translated_name,
                "image": product['image'],  # image path çevirilmeden kalıyor
                "description": translated_description
            }

            translated_products.append(translated_product)

        return translated_products

    def update_product_info(self, product_id, **kwargs):
        self.product_repo.update_product(product_id, **kwargs)

    def delete_product(self, product_id):
        self.product_repo.delete_product(product_id)
