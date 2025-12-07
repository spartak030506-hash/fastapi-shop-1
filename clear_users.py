"""
Скрипт для очистки всех пользователей из БД (для тестирования)
ВНИМАНИЕ: Удалит ВСЕ пользователей и их токены!
"""
import asyncio
from sqlalchemy import text
from app.core.database import engine


async def clear_all_users():
    async with engine.connect() as conn:
        # Сначала удаляем refresh токены (из-за FK constraint)
        await conn.execute(text("DELETE FROM refresh_tokens"))
        print("✅ Удалены все refresh токены")

        # Потом удаляем пользователей
        result = await conn.execute(text("DELETE FROM users"))
        await conn.commit()
        print(f"✅ Удалено пользователей: {result.rowcount}")

        # Проверяем
        count_result = await conn.execute(text("SELECT COUNT(*) FROM users"))
        count = count_result.scalar()
        print(f"📊 Осталось пользователей в БД: {count}")


async def show_users():
    async with engine.connect() as conn:
        result = await conn.execute(
            text("SELECT email, first_name, last_name, role FROM users")
        )
        rows = result.fetchall()

        if not rows:
            print("📭 Пользователей в БД нет")
        else:
            print(f"\n📋 Всего пользователей: {len(rows)}")
            print("-" * 80)
            for row in rows:
                print(f"Email: {row[0]}, Имя: {row[1]} {row[2]}, Роль: {row[3]}")
            print("-" * 80)


async def main():
    print("\n" + "=" * 80)
    print("🗑️  ОЧИСТКА БАЗЫ ДАННЫХ ПОЛЬЗОВАТЕЛЕЙ")
    print("=" * 80 + "\n")

    print("📋 Текущие пользователи:")
    await show_users()

    print("\n⚠️  ВНИМАНИЕ: Сейчас будут удалены ВСЕ пользователи!")
    confirm = input("\n❓ Продолжить? (yes/no): ")

    if confirm.lower() in ['yes', 'y', 'да', 'д']:
        await clear_all_users()
        print("\n✅ Очистка завершена!")
        print("\n📋 Проверка:")
        await show_users()
    else:
        print("\n❌ Отменено")


if __name__ == "__main__":
    asyncio.run(main())
