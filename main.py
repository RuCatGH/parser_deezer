import aiohttp
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import ParseMode
from datetime import datetime
from dotenv import load_dotenv
import os
import io

load_dotenv()

API_TOKEN = os.getenv('API_TOKEN_TELEGRAM')
CHAT_ID  = os.getenv('CHAT_ID')
start_track_id = int(os.getenv('START_TRACK_ID'))
end_track_id = int(os.getenv('END_TRACK_ID'))
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
deezer_api_url = 'https://api.deezer.com/track/{}'

async def get_image_from_url(image_url, session):
    async with session.get(image_url) as response:
        if response.status == 200:
            # Читаем данные изображения
            image_data = await response.read()

            # Создаем объект InputFile для отправки изображения
            photo = types.InputFile(io.BytesIO(image_data), filename='photo.jpg')

            # Отправляем изображение в чат
            return photo
        else:
            await bot.send_message(CHAT_ID, "Не удалось загрузить изображение.")

async def fetch_track_data(session, track_id):
    async with session.get(deezer_api_url.format(track_id)) as response:
        if response.status == 200:
            return await response.json()
        return None

async def process_track(session, track_id):
    print(track_id)
    track_data = await fetch_track_data(session, track_id)
    try:
        if track_data['error']['message'] == 'no data':
            return
    except:
        pass

    if not track_data:
        return

    release_date = track_data.get('release_date')
    if release_date and release_date > datetime.today().strftime('%Y-%m-%d'):
        artist_name = track_data['artist']['name']
        title = track_data['title']
        isrc = track_data['isrc']
        md5_image = track_data['md5_image']
        url_image = f'https://e-cdn-images.dzcdn.net/images/cover/{md5_image}/264x264-000000-80-0-0.jpg'

        message = f"Artist: {artist_name}\nTitle: {title}\nISRC: {isrc}"
        await bot.send_photo(chat_id=CHAT_ID,caption=message, photo=await get_image_from_url(url_image, session), parse_mode=ParseMode.MARKDOWN)

async def main():
    await bot.send_message(chat_id= os.getenv('CHAT_ID'), text='Бот запущен', parse_mode=ParseMode.MARKDOWN)
    # Создаем одну сессию для всех запросов
    chunk_size = 100
    tasks = []

    async with aiohttp.ClientSession() as session:
        for track_id in range(start_track_id, end_track_id):
            tasks.append(process_track(session, track_id))
            if len(tasks) == chunk_size:
                await asyncio.gather(*tasks)
                tasks = []

        # Если остались какие-то оставшиеся задачи (не делится нацело на 50)
        if tasks:
            await asyncio.gather(*tasks)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(main())
    loop.create_task(dp.start_polling())
    loop.run_forever()
