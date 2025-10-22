#!/usr/bin/env python
"""
Seed script to populate default categories and subcategories for Wants/Offers marketplace.
Run from backend directory:
    python scripts/seed_categories.py
"""

import sys
import os
from pathlib import Path

# Add parent directory to path so we can import backend modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database import SessionLocal
from backend.models import Category, ListingSection
from backend.crud import upsert_category


WANTS_CATEGORIES = [
    {
        "name": "Техника и электроника",
        "slug": "electronics",
        "subcategories": [
            {"name": "Смартфоны", "slug": "phones"},
            {"name": "Ноутбуки и ПК", "slug": "computers"},
            {"name": "Планшеты", "slug": "tablets"},
            {"name": "Телевизоры", "slug": "tvs"},
            {"name": "Прочее", "slug": "electronics-other"},
        ]
    },
    {
        "name": "Одежда и обувь",
        "slug": "clothing",
        "subcategories": [
            {"name": "Мужская одежда", "slug": "mens"},
            {"name": "Женская одежда", "slug": "womens"},
            {"name": "Детская одежда", "slug": "kids"},
            {"name": "Обувь", "slug": "shoes"},
            {"name": "Аксессуары", "slug": "accessories"},
        ]
    },
    {
        "name": "Мебель и домашний быт",
        "slug": "furniture",
        "subcategories": [
            {"name": "Мебель", "slug": "furniture-items"},
            {"name": "Кухонные приборы", "slug": "kitchen"},
            {"name": "Посуда и столовые приборы", "slug": "dishes"},
            {"name": "Текстиль", "slug": "textiles"},
        ]
    },
    {
        "name": "Книги и медиа",
        "slug": "books",
        "subcategories": [
            {"name": "Художественные", "slug": "fiction"},
            {"name": "Учебные", "slug": "textbooks"},
            {"name": "Музыка и фильмы", "slug": "media"},
            {"name": "Журналы", "slug": "magazines"},
        ]
    },
    {
        "name": "Спорт и активный отдых",
        "slug": "sports",
        "subcategories": [
            {"name": "Велосипеды", "slug": "bikes"},
            {"name": "Спортивное оборудование", "slug": "equipment"},
            {"name": "Туристический инвентарь", "slug": "tourism"},
            {"name": "Прочее", "slug": "sports-other"},
        ]
    },
    {
        "name": "Услуги",
        "slug": "services",
        "subcategories": [
            {"name": "Репетиторство", "slug": "tutoring"},
            {"name": "Ремонт и строительство", "slug": "repair"},
            {"name": "Дизайн и творчество", "slug": "design"},
            {"name": "Прочие услуги", "slug": "services-other"},
        ]
    }
]

OFFERS_CATEGORIES = [
    {
        "name": "Техника и электроника",
        "slug": "electronics",
        "subcategories": [
            {"name": "Смартфоны", "slug": "phones"},
            {"name": "Ноутбуки и ПК", "slug": "computers"},
            {"name": "Планшеты", "slug": "tablets"},
            {"name": "Телевизоры", "slug": "tvs"},
            {"name": "Прочее", "slug": "electronics-other"},
        ]
    },
    {
        "name": "Одежда и обувь",
        "slug": "clothing",
        "subcategories": [
            {"name": "Мужская одежда", "slug": "mens"},
            {"name": "Женская одежда", "slug": "womens"},
            {"name": "Детская одежда", "slug": "kids"},
            {"name": "Обувь", "slug": "shoes"},
            {"name": "Аксессуары", "slug": "accessories"},
        ]
    },
    {
        "name": "Мебель и домашний быт",
        "slug": "furniture",
        "subcategories": [
            {"name": "Мебель", "slug": "furniture-items"},
            {"name": "Кухонные приборы", "slug": "kitchen"},
            {"name": "Посуда и столовые приборы", "slug": "dishes"},
            {"name": "Текстиль", "slug": "textiles"},
        ]
    },
    {
        "name": "Книги и медиа",
        "slug": "books",
        "subcategories": [
            {"name": "Художественные", "slug": "fiction"},
            {"name": "Учебные", "slug": "textbooks"},
            {"name": "Музыка и фильмы", "slug": "media"},
            {"name": "Журналы", "slug": "magazines"},
        ]
    },
    {
        "name": "Спорт и активный отдых",
        "slug": "sports",
        "subcategories": [
            {"name": "Велосипеды", "slug": "bikes"},
            {"name": "Спортивное оборудование", "slug": "equipment"},
            {"name": "Туристический инвентарь", "slug": "tourism"},
            {"name": "Прочее", "slug": "sports-other"},
        ]
    },
    {
        "name": "Услуги",
        "slug": "services",
        "subcategories": [
            {"name": "Репетиторство", "slug": "tutoring"},
            {"name": "Ремонт и строительство", "slug": "repair"},
            {"name": "Дизайн и творчество", "slug": "design"},
            {"name": "Прочие услуги", "slug": "services-other"},
        ]
    }
]

# Add modern categories for seeding
MODERN_CATEGORIES = [
    {
        "name": "Технологии и вычисления",
        "slug": "tech",
        "subcategories": [
            {"name": "Серверы и вычислительные мощности", "slug": "computing"},
            {"name": "Облачные ресурсы и хостинг", "slug": "cloud"},
            {"name": "Электроника и оборудование", "slug": "hardware"},
            {"name": "Ноутбуки и ПК", "slug": "computers"},
            {"name": "Смартфоны и планшеты", "slug": "mobile"},
            {"name": "Прочее", "slug": "tech-other"},
        ],
    },
    {
        "name": "Программное обеспечение и лицензии",
        "slug": "software",
        "subcategories": [
            {"name": "SaaS и подписки", "slug": "saas"},
            {"name": "Dev-инструменты", "slug": "devtools"},
            {"name": "AI и аналитика", "slug": "ai-tools"},
            {"name": "Дизайн и мультимедиа", "slug": "design-tools"},
            {"name": "Прочее ПО", "slug": "software-other"},
        ],
    },
    {
        "name": "Образование и экспертиза",
        "slug": "education",
        "subcategories": [
            {"name": "Курсы и материалы", "slug": "courses"},
            {"name": "Менторство и консультации", "slug": "mentorship"},
            {"name": "Исследования и аналитика", "slug": "research"},
            {"name": "Репетиторство и обучение", "slug": "teaching"},
            {"name": "Прочее", "slug": "education-other"},
        ],
    },
    {
        "name": "Инфраструктура и ресурсы",
        "slug": "infrastructure",
        "subcategories": [
            {"name": "Помещения и коворкинги", "slug": "space"},
            {"name": "Оборудование и инструменты", "slug": "equipment"},
            {"name": "Транспорт и логистика", "slug": "transport"},
            {"name": "Энергоресурсы и связь", "slug": "utilities"},
            {"name": "Прочее", "slug": "infra-other"},
        ],
    },
    {
        "name": "Услуги и сотрудничество",
        "slug": "services",
        "subcategories": [
            {"name": "Разработка и IT", "slug": "development"},
            {"name": "Дизайн и брендинг", "slug": "design"},
            {"name": "Маркетинг и PR", "slug": "marketing"},
            {"name": "Юридическая и финансовая помощь", "slug": "legal"},
            {"name": "Техническая поддержка", "slug": "support"},
            {"name": "Прочие услуги", "slug": "services-other"},
        ],
    },
    {
        "name": "Товары и материалы",
        "slug": "items",
        "subcategories": [
            {"name": "Мебель и обустройство", "slug": "furniture"},
            {"name": "Одежда и экипировка", "slug": "gear"},
            {"name": "Инструменты и расходники", "slug": "tools"},
            {"name": "Спорт и отдых", "slug": "sports"},
            {"name": "Прочее", "slug": "items-other"},
        ],
    },
    {
        "name": "Бытовая техника и транспорт",
        "slug": "appliances",
        "subcategories": [
            {"name": "Стиральные и посудомоечные машины", "slug": "washers"},
            {"name": "Холодильники и морозильники", "slug": "fridges"},
            {"name": "Пылесосы и уборочная техника", "slug": "cleaning"},
            {"name": "Автомобили и мотоциклы", "slug": "vehicles"},
            {"name": "Электросамокаты и велосипеды", "slug": "mobility"},
            {"name": "Прочее", "slug": "appliances-other"},
        ],
    },
    {
        "name": "Недвижимость и аренда",
        "slug": "realestate",
        "subcategories": [
            {"name": "Жильё (долгосрочная аренда)", "slug": "housing"},
            {"name": "Краткосрочная аренда", "slug": "short-rent"},
            {"name": "Офисы и помещения", "slug": "office"},
            {"name": "Склады и гаражи", "slug": "storage"},
            {"name": "Прочее", "slug": "realestate-other"},
        ],
    },
    {
        "name": "Финансы и взаимопомощь",
        "slug": "finance",
        "subcategories": [
            {"name": "Взаимные займы", "slug": "loans"},
            {"name": "Инвестиции и партнёрство", "slug": "investments"},
            {"name": "Совместные покупки", "slug": "group-buys"},
            {"name": "Донаты и пожертвования", "slug": "donations"},
            {"name": "Прочее", "slug": "finance-other"},
        ],
    },
]


def seed_categories(db, section: ListingSection, categories_data):
    """Seed categories for a given section"""
    print(f"\n📦 Seeding categories for '{section.value}'...")

    for sort_order, cat_data in enumerate(categories_data):
        cat_name = cat_data["name"]
        cat_slug = cat_data["slug"]

        # Create parent category
        parent = upsert_category(
            db,
            slug=cat_slug,
            section=section.value,
            name=cat_name,
            parent_id=None,
            sort_order=sort_order
        )

        # Refresh to ensure we have the actual id value
        db.refresh(parent)
        parent_id_int: int = parent.id  # type: ignore

        print(f"  ✓ {cat_name} (id={parent_id_int})")

        # Create subcategories
        for sub_order, subcat_data in enumerate(cat_data.get("subcategories", [])):
            sub_name = subcat_data["name"]
            sub_slug = subcat_data["slug"]

            subcat = upsert_category(
                db,
                slug=sub_slug,
                section=section.value,
                name=sub_name,
                parent_id=parent_id_int,
                sort_order=sub_order
            )
            print(f"    ✓ {sub_name} (id={subcat.id})")


def main():
    db = SessionLocal()
    try:
        print("🌱 Starting category seeding...")

        # Seed wants categories
        seed_categories(db, ListingSection.WANT, WANTS_CATEGORIES)

        # Seed offers categories
        seed_categories(db, ListingSection.OFFER, OFFERS_CATEGORIES)

        # Seed modern categories
        seed_categories(db, ListingSection.WANT, MODERN_CATEGORIES)
        seed_categories(db, ListingSection.OFFER, MODERN_CATEGORIES)

        print("\n✅ Category seeding completed successfully!")

    except Exception as e:
        print(f"❌ Error during seeding: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
