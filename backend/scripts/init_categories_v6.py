#!/usr/bin/env python3
"""
Initialize Categories v6 data
Creates category versions and populates categories for both permanent and temporary exchanges.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from backend.database import engine


def init_categories_v6():
    """Initialize v6 category system with data using raw SQL"""

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        print("Creating category version v6.0...")
        # Create v6.0 version using raw SQL
        db.execute(text("""
            INSERT INTO category_versions (version, is_active, description, created_at)
            VALUES ('v6.0', true, 'Initial v6 category system with expanded temporary and permanent exchanges', NOW())
            ON CONFLICT (version) DO NOTHING
        """))

        # Get version id
        result = db.execute(text("SELECT id FROM category_versions WHERE version = 'v6.0'"))
        version_row = result.fetchone()
        if not version_row:
            raise Exception("Failed to create or find category version")
        version_id = version_row[0]

        print(f"Category version created with id: {version_id}")

        # TEMPORARY EXCHANGE CATEGORIES (с возвратом) - tuples for easier insertion
        temporary_categories = [
            ("bicycles", "Велосипеды, самокаты, гироскутеры", "🚗 Транспорт и мобильность", "🚗"),
            ("electric_transport", "Электросамокаты, электровелосипеды", "🚗 Транспорт и мобильность", "🚗"),
            ("carsharing", "Каршеринг, аренда прицепов, спецтехники", "🚗 Транспорт и мобильность", "🚗"),
            ("hand_tools", "Ручные и электроинструменты", "🔧 Инструменты и оборудование", "🔧"),
            ("printers_equipment", "3D-принтеры, станки, лабораторное оборудование", "🔧 Инструменты и оборудование", "🔧"),
            ("construction_tools", "Оснащение для стройки, ремонта, мероприятий", "🔧 Инструменты и оборудование", "🔧"),
            ("photo_equipment", "Фотоаппараты, объективы, дроны", "📷 Фото-, видео-, аудио-техника", "📷"),
            ("video_audio", "Свет, звук, микрофоны, рекордеры", "📷 Фото-, видео-, аудио-техника", "📷"),
            ("production_kits", "Комплекты для съёмок, трансляций, подкастов", "📷 Фото-, видео-, аудио-техника", "📷"),
            ("cloud_resources", "Облачные GPU/CPU, хостинг, storage", "💻 Цифровые и вычислительные ресурсы", "💻"),
            ("api_access", "Временный доступ к API, ML-моделям, инструментам", "💻 Цифровые и вычислительные ресурсы", "💻"),
            ("software_licenses", "Подписки, лицензии, токены с ограниченным сроком", "💻 Цифровые и вычислительные ресурсы", "💻"),
            ("network_resources", "Сетевые или энергетические мощности, интернет-каналы", "💻 Цифровые и вычислительные ресурсы", "💻"),
            ("money_crypto", "Деньги, криптовалюта, токены — с возвратом в том же объёме", "💸 Финансы и взаимные займы", "💸"),
            ("trusted_equivalent", "Используются как доверенный эквивалент ресурса", "💸 Финансы и взаимные займы", "💸"),
            ("tutoring", "Репетиторство, консультации, менторство", "👥 Услуги и навыки", "👥"),
            ("task_execution", "Исполнение задач, помощь, участие в проектах", "👥 Услуги и навыки", "👥"),
            ("time_resource", "Время человека как ограниченный ресурс", "👥 Услуги и навыки", "👥"),
            ("housing_rental", "Аренда жилья, офисов, складов", "🏠 Пространства и помещения", "🏠"),
            ("coworking_spaces", "Коворкинги, студии, площадки для мероприятий", "🏠 Пространства и помещения", "🏠"),
            ("pet_sitting", "Передержка питомцев, полив растений", "🐾 Уход за живыми объектами", "🐾"),
            ("temporary_care", "Временный уход", "🐾 Уход за живыми объектами", "🐾"),
            ("sports_equipment", "Спортивный инвентарь, палатки, кемпинг", "🎯 Спорт, отдых и досуг", "🎯"),
            ("board_games", "Настольные игры, VR, музыкальные инструменты", "🎯 Спорт, отдых и досуг", "🎯"),
            ("props_rental", "Прокат реквизита, костюмов, сценических аксессуаров", "🎯 Спорт, отдых и досуг", "🎯"),
        ]

        print("Creating temporary categories...")
        # Insert temporary categories using raw SQL
        for sort_order, (slug, name, group_name, emoji) in enumerate(temporary_categories):
            db.execute(text("""
                INSERT INTO categories_v6 (version_id, slug, name, "group", emoji, exchange_type, is_active, sort_order, created_at)
                VALUES (:version_id, :slug, :name, :group_name, :emoji, 'TEMPORARY', TRUE, :sort_order, NOW())
                ON CONFLICT (version_id, exchange_type, slug) DO NOTHING
            """), {
                'version_id': version_id,
                'slug': slug,
                'name': name,
                'group_name': group_name,
                'emoji': emoji,
                'sort_order': sort_order
            })

        # PERMANENT EXCHANGE CATEGORIES (без возврата) - tuples for easier insertion
        permanent_categories = [
            ("personal_transport", "Личные и спецтранспортные средства", "🚗 Транспорт и техника", "🚗"),
            ("electric_vehicles", "Электротранспорт, дроны, техника для хобби", "🚗 Транспорт и техника", "🚗"),
            ("parts_consumables", "Запчасти, комплектующие, расходники", "🚗 Транспорт и техника", "🚗"),
            ("hand_power_tools", "Ручные, электро-, строительные, лабораторные инструменты", "🔧 Инструменты и оборудование", "🔧"),
            ("production_facilities", "Производственные и ремесленные установки", "🔧 Инструменты и оборудование", "🔧"),
            ("building_materials", "Строительные материалы и элементы (двери, окна, панели, крепёж)", "🔧 Инструменты и оборудование", "🔧"),
            ("photo_equipment", "Фотоаппараты, оптика, микрофоны", "📷 Фото-, видео-, аудио-техника", "📷"),
            ("lighting_equipment", "Осветительные приборы, звукозаписывающая техника", "📷 Фото-, видео-, аудио-техника", "📷"),
            ("software_programs", "Программы, исходный код, шаблоны, дизайн", "💾 Цифровые, креативные и интеллектуальные активы", "💾"),
            ("media_content", "Медиа, музыка, видео, NFT, цифровые коллекции", "💾 Цифровые, креативные и интеллектуальные активы", "💾"),
            ("intellectual_property", "Авторские права, бессрочные лицензии", "💾 Цифровые, креативные и интеллектуальные активы", "💾"),
            ("completed_projects", "Завершённые проекты, контент, дизайн, разработка", "👥 Услуги и навыки", "👥"),
            ("services_work", "Ремонт, монтаж, обучение — с передачей результата", "👥 Услуги и навыки", "👥"),
            ("property", "Земля, дома, квартиры, студии, гаражи", "🏠 Недвижимость и пространство", "🏠"),
            ("property_rights", "Право собственности или доля", "🏠 Недвижимость и пространство", "🏠"),
            ("garden_equipment", "Садовая техника, полив, мебель для сада", "🪴 Дом, сад и строительство", "🪴"),
            ("decor_elements", "Декор, ограждения, строительные материалы", "🪴 Дом, сад и строительство", "🪴"),
            ("furniture_appliances", "Мебель, бытовая техника, освещение", "🛋️ Быт, мебель и интерьер", "🛋️"),
            ("decor_textiles", "Декор, текстиль, ковры, зеркала", "🛋️ Быт, мебель и интерьер", "🛋️"),
            ("clothing_footwear", "Одежда, обувь, аксессуары, украшения", "👕 Одежда, мода и личные вещи", "👕"),
            ("vintage_luxury", "Винтаж, мода premium, коллекционные вещи", "👕 Одежда, мода и личные вещи", "👕"),
            ("games_collectibles", "Настольные игры, фигурки, комиксы, карточки", "🎮 Хобби, игры и коллекции", "🎮"),
            ("models_merch", "Модели, игрушки, фан-мерч, подписные наборы", "🎮 Хобби, игры и коллекции", "🎮"),
            ("physical_media", "Книги, журналы, ноты, винил, CD, DVD", "📚 Книги, музыка и медиа", "📚"),
            ("antiques_rare", "Антикварные и редкие издания", "📚 Книги, музыка и медиа", "📚"),
            ("beauty_cosmetics", "Косметика, парфюмерия, уходовые гаджеты", "🧴 Здоровье, красота и уход", "🧴"),
            ("health_devices", "Аппараты для здоровья, wellness-техника", "🧴 Здоровье, красота и уход", "🧴"),
            ("plants_animals", "Растения, семена, питомцы, аквариумные объекты", "🌱 Живые объекты и природа", "🌱"),
            ("breeding_care", "Разведение и уход", "🌱 Живые объекты и природа", "🌱"),
            ("farm_products", "Фермерская продукция, заготовки, мед, зерно, семена", "🍎 Продукты и сельхозтовары", "🍎"),
            ("natural_resources", "Обмен натуральными продуктами и ресурсами", "🍎 Продукты и сельхозтовары", "🍎"),
            ("courses_materials", "Курсы, методики, учебные материалы, книги", "📚 Образовательные ресурсы и знания", "📚"),
            ("intellectual_constructions", "Авторские наработки, интеллектуальные конструкции", "📚 Образовательные ресурсы и знания", "📚"),
            ("money_crypto", "Деньги, криптовалюта, токены", "⚖️ Финансы и ценные активы", "⚖️"),
            ("securities_assets", "Ценные бумаги, доли, активы", "⚖️ Финансы и ценные активы", "⚖️"),
        ]

        print("Creating permanent categories...")
        # Insert permanent categories using raw SQL
        for sort_order, (slug, name, group_name, emoji) in enumerate(permanent_categories):
            db.execute(text("""
                INSERT INTO categories_v6 (version_id, slug, name, "group", emoji, exchange_type, is_active, sort_order, created_at)
                VALUES (:version_id, :slug, :name, :group_name, :emoji, 'PERMANENT', TRUE, :sort_order, NOW())
                ON CONFLICT (version_id, exchange_type, slug) DO NOTHING
            """), {
                'version_id': version_id,
                'slug': slug,
                'name': name,
                'group_name': group_name,
                'emoji': emoji,
                'sort_order': sort_order
            })

        # Create legacy mappings for migration
        legacy_mappings = [
            ("electronics", "photo_equipment", "PERMANENT", 0.9),
            ("electronics", "lighting_equipment", "PERMANENT", 0.8),
            ("money", "money_crypto", "PERMANENT", 1.0),
            ("furniture", "furniture_appliances", "PERMANENT", 0.9),
            ("furniture", "decor_textiles", "PERMANENT", 0.7),
            ("transport", "personal_transport", "PERMANENT", 0.9),
            ("transport", "electric_vehicles", "PERMANENT", 0.8),
            ("services", "services_work", "PERMANENT", 0.9),
            ("services", "completed_projects", "PERMANENT", 0.8),
            ("electronics", "photo_equipment", "TEMPORARY", 0.7),
            ("electronics", "video_audio", "TEMPORARY", 0.7),
            ("money", "money_crypto", "TEMPORARY", 0.8),
            ("money", "trusted_equivalent", "TEMPORARY", 0.6),
            ("furniture", "furniture_appliances", "TEMPORARY", 0.7),
            ("transport", "bicycles", "TEMPORARY", 0.8),
            ("transport", "electric_transport", "TEMPORARY", 0.9),
            ("services", "tutoring", "TEMPORARY", 0.8),
            ("services", "task_execution", "TEMPORARY", 0.8),
        ]

        print("Creating legacy mappings...")
        # Insert legacy mappings using raw SQL
        for legacy, new_slug, exchange_type, confidence in legacy_mappings:
            db.execute(text("""
                INSERT INTO category_mappings (legacy_category, new_category_slug, exchange_type, confidence, created_at)
                VALUES (:legacy, :new_slug, :exchange_type, :confidence, NOW())
                ON CONFLICT (legacy_category, new_category_slug, exchange_type) DO NOTHING
            """), {
                'legacy': legacy,
                'new_slug': new_slug,
                'exchange_type': exchange_type,
                'confidence': confidence
            })

        db.commit()
        print("✅ Categories v6 initialized successfully!")
        print(f"Created {len(temporary_categories)} temporary categories")
        print(f"Created {len(permanent_categories)} permanent categories")
        print(f"Created {len(legacy_mappings)} legacy mappings")

    except Exception as e:
        db.rollback()
        print(f"❌ Error initializing categories: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    init_categories_v6()
