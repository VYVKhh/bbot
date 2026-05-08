# tools/bin_lookup.py
import aiohttp
from aiogram import Router, types
from aiogram.filters import Command

router = Router()

async def get_bin_info(bin_num: str):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://bins.antipublic.cc/bins/{bin_num}", timeout=5) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {
                        "brand": data.get("brand", "Unknown"),
                        "type": data.get("type", "Unknown"),
                        "level": data.get("level", "Unknown"),
                        "bank": data.get("bank", "Unknown"),
                        "country": data.get("country_name", "Unknown"),
                        "flag": data.get("country_flag", "🏳")
                    }
    except:
        pass
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://lookup.binlist.net/{bin_num}", timeout=5) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {
                        "brand": data.get('scheme', 'Unknown'),
                        "type": data.get('type', 'Unknown'),
                        "level": data.get('brand', 'Unknown'),
                        "bank": data.get('bank', {}).get('name', 'Unknown'),
                        "country": data.get('country', {}).get('name', 'Unknown'),
                        "flag": data.get('country', {}).get('emoji', '🏳')
                    }
    except:
        pass
    return {
        "brand": "Unknown",
        "type": "Unknown",
        "level": "Unknown",
        "bank": "Unknown",
        "country": "Unknown",
        "flag": "🏳"
    }

@router.message(Command("bin"))
async def bin_lookup(message: types.Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Usage: /bin <first 6 digits>")
        return
    bin_num = args[1].strip()[:6]
    if not bin_num.isdigit() or len(bin_num) != 6:
        await message.answer("BIN must be 6 digits.")
        return
    info = await get_bin_info(bin_num)
    text = (
        f"🔎 **BIN Lookup** `{bin_num}`\n"
        f"🏦 Bank: {info['bank']}\n"
        f"💳 Brand: {info['brand']}\n"
        f"📊 Type: {info['type']}\n"
        f"💎 Level: {info['level']}\n"
        f"🌍 Country: {info['flag']} {info['country']}"
    )
    await message.answer(text, parse_mode="Markdown")