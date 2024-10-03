from connector import Database
from PIL import Image

class UserRepository:
    def __init__(self):
        self.db = Database.get_connection()
        self.cursor = self.db.cursor()

    def create_user(self, name, username, email, password, city=None, region=None):
        query = """
        INSERT INTO user (name, username, email, password, city, region, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
        """
        values = (name, username, email, password, city, region)
        self.cursor.execute(query, values)
        self.db.commit()

    def get_user(self, user_id):
        query = "SELECT * FROM user WHERE id = %s"
        self.cursor.execute(query, (user_id,))
        return self.cursor.fetchone()
    
    def get_user_region(self, user_id):
        query = "SELECT city FROM user WHERE id = %s"
        self.cursor.execute(query, (user_id,))
        result = self.cursor.fetchone()

        # Check if a result was returned
        if result:
            return result[0]  # Return the city
        else:
            return None 
    
    def get_user_by_username(self, username):
        query = "SELECT id, username, password FROM user WHERE username = %s"
        self.cursor.execute(query, (username,))
        return self.cursor.fetchone()

    def update_user(self, user_id, name=None, username=None, email=None, city=None, region=None):
        updates = []
        values = []
        if name:
            updates.append("name=%s")
            values.append(name)
        if username:
            updates.append("username=%s")
            values.append(username)
        if email:
            updates.append("email=%s")
            values.append(email)
        if city:
            updates.append("city=%s")
            values.append(city)
        if region:
            updates.append("region=%s")
            values.append(region)

        if updates:
            query = f"UPDATE user SET {', '.join(updates)}, updated_at=NOW() WHERE id=%s"
            values.append(user_id)
            self.cursor.execute(query, values)
            self.db.commit()

    def delete_user(self, user_id):
        query = "DELETE FROM user WHERE id = %s"
        self.cursor.execute(query, (user_id,))
        self.db.commit()

    def __del__(self):
        self.db.close()


class ProductRepository:
    def __init__(self):
        self.db = Database.get_connection()
        self.cursor = self.db.cursor()

    def create_product(self, user_id, header_text, image_path, description):
        query = """
        INSERT INTO product (user_id, header_text, image_url, enhanced_image_url, description, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
        """
        values = (user_id, header_text, image_path, "", description)
        self.cursor.execute(query, values)
        self.db.commit()

    def get_product(self, product_id):
        query = "SELECT * FROM product WHERE id = %s"
        self.cursor.execute(query, (product_id,))
        return self.cursor.fetchone()

    def update_product(self, product_id, header_text=None, image_url=None):
        updates = []
        values = []
        if header_text:
            updates.append("header_text=%s")
            values.append(header_text)
        if image_url:
            updates.append("image_url=%s")
            values.append(image_url)

        if updates:
            query = f"UPDATE product SET {', '.join(updates)}, updated_at=NOW() WHERE id=%s"
            values.append(product_id)
            self.cursor.execute(query, values)
            self.db.commit()
            
    # New function to fetch all products in the desired format
    def get_all_products_as_list(self):
        query = "SELECT user_id, header_text, image_url, description FROM product"
        self.cursor.execute(query)
        products = self.cursor.fetchall()

        # Convert result to the desired format
        result = [
            {"user": user_id, "name": header_text, "image": Image.open(image_url), "description": description}
            for (user_id, header_text, image_url, description) in products
        ]
        return result

    def delete_product(self, product_id):
        query = "DELETE FROM product WHERE id = %s"
        self.cursor.execute(query, (product_id,))
        self.db.commit()

    def __del__(self):
        self.cursor.close()
        self.db.close()
