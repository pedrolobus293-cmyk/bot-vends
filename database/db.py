import aiosqlite
import os

DB_PATH = "database/sales_bot.db"

async def setup_db():
    # Ensure the directory exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                price REAL NOT NULL,
                pix_key TEXT NOT NULL,
                buyer_message TEXT NOT NULL,
                role_id INTEGER NOT NULL,
                button_name TEXT NOT NULL DEFAULT 'Comprar',
                image_url TEXT,
                embed_color INTEGER DEFAULT 3447003
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS purchases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                status TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Migration: Check if columns exist
        async with db.execute("PRAGMA table_info(products)") as cursor:
            columns = [row[1] for row in await cursor.fetchall()]
            if "image_url" not in columns:
                await db.execute("ALTER TABLE products ADD COLUMN image_url TEXT")
            if "embed_color" not in columns:
                await db.execute("ALTER TABLE products ADD COLUMN embed_color INTEGER DEFAULT 3447003")
        
        await db.commit()

async def add_product(name, description, price, pix_key, buyer_message, role_id, button_name='Comprar', image_url=None, embed_color=3447003):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO products (name, description, price, pix_key, buyer_message, role_id, button_name, image_url, embed_color) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (name, description, price, pix_key, buyer_message, role_id, button_name, image_url, embed_color)
        )
        await db.commit()

async def edit_product(product_id, name, description, price, pix_key, buyer_message, role_id, button_name, image_url=None, embed_color=3447003):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE products SET name=?, description=?, price=?, pix_key=?, buyer_message=?, role_id=?, button_name=?, image_url=?, embed_color=? WHERE id=?",
            (name, description, price, pix_key, buyer_message, role_id, button_name, image_url, embed_color, product_id)
        )
        await db.commit()

async def remove_product(product_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM products WHERE id=?", (product_id,))
        await db.commit()

async def get_all_products():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM products") as cursor:
            return await cursor.fetchall()

async def get_product(product_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM products WHERE id=?", (product_id,)) as cursor:
            return await cursor.fetchone()

async def create_purchase(user_id, product_id):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO purchases (user_id, product_id, status) VALUES (?, ?, 'PENDING')",
            (user_id, product_id)
        )
        purchase_id = cursor.lastrowid
        await db.commit()
        return purchase_id

async def update_purchase_status(purchase_id, status):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE purchases SET status=? WHERE id=?", (status, purchase_id))
        await db.commit()

async def get_purchase(purchase_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM purchases WHERE id=?", (purchase_id,)) as cursor:
            return await cursor.fetchone()
