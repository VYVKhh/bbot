# main.py
import asyncio
import importlib
import secrets
import random
from pathlib import Path
from typing import Dict, Any, List, Tuple

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm import state
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message, BufferedInputFile, FSInputFile, InputMediaPhoto
from aiogram.enums import ParseMode

import aiohttp
import database as db
from admin_handlers import router as admin_router

BOT_TOKEN = "8273595803:AAH9jb4PGdNn6U0zkT7vyl7_5TZKFmAXXBw"
DEV_NAME = "𝙅𝘼𝙁𝘼𝙍"
DEV_LINK = "https://t.me/VYV_K"
GATER_NAME = "𝗞𝗜𝗩𝗘𝗡"
GATER_LINK = "https://t.me/CYU_0"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

temp_storage: Dict[str, Dict[str, Any]] = {}
scan_tasks: Dict[int, asyncio.Task] = {}

class BulkScanState(state.StatesGroup):
    scanning = state.State()

async def get_bin_info(bin_num: str):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://bins.antipublic.cc/bins/{bin_num}", timeout=3) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    brand = data.get("brand", "UNKNOWN")
                    card_type = data.get("type", "UNKNOWN")
                    level = data.get("level", "UNKNOWN")
                    bank = data.get("bank", "UNKNOWN")
                    country_name = data.get("country_name", "UNKNOWN")
                    country_flag = data.get("country_flag", "🏳️")
                    bin_info = f"{brand} - {card_type} - {level}"
                    return bin_info, bank, f"{country_flag} {country_name}"
    except:
        pass
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://lookup.binlist.net/{bin_num}", timeout=3) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    brand = data.get('scheme', 'UNKNOWN')
                    card_type = data.get('type', 'UNKNOWN')
                    level = data.get('brand', 'UNKNOWN')
                    bank = data.get('bank', {}).get('name', 'UNKNOWN')
                    country = data.get('country', {}).get('name', 'UNKNOWN')
                    flag = data.get('country', {}).get('emoji', '🏳️')
                    bin_info = f"{brand} - {card_type} - {level}"
                    return bin_info, bank, f"{flag} {country}"
    except:
        pass
    if bin_num == "539689":
        return "MASTERCARD - DEBIT - PLATINUM", "COASTAL COMMUNITY BANK", "🇺🇸 United States"
    return "UNKNOWN - UNKNOWN - UNKNOWN", "UNKNOWN", "🏳️ UNKNOWN"

GATES: Dict[str, Dict[str, Any]] = {}

def load_gates():
    gates_dir = Path("gates")
    if not gates_dir.exists():
        return
    for file in gates_dir.glob("*.py"):
        if file.name == "__init__.py":
            continue
        module_name = f"gates.{file.stem}"
        try:
            module = importlib.import_module(module_name)
            cmd = getattr(module, "CMD", None)
            if cmd:
                GATES[cmd] = {
                    "module": module,
                    "name": getattr(module, "NAME", cmd),
                    "price": getattr(module, "PRICE", "0.0"),
                    "cmd": cmd,
                    "delay": getattr(module, "DELAY", 1.0),
                    "fee_single": getattr(module, "FEE_SINGLE", 1),
                    "fee_bulk": getattr(module, "FEE_BULK", 1)
                }
        except Exception as e:
            print(f"Error loading {file.stem}: {e}")

load_gates()

async def send_or_edit_with_image(chat_id: int, message_id: int, text: str, reply_markup=None):
    images_dir = Path("images")
    photo = None
    if images_dir.exists() and any(images_dir.iterdir()):
        image_files = [f for f in images_dir.iterdir() if f.suffix.lower() in ['.jpg', '.jpeg', '.png']]
        if image_files:
            image_path = random.choice(image_files)
            photo = FSInputFile(image_path)
    if message_id:
        if photo:
            media = InputMediaPhoto(media=photo, caption=text, parse_mode=ParseMode.MARKDOWN)
            await bot.edit_message_media(media=media, chat_id=chat_id, message_id=message_id, reply_markup=reply_markup)
        else:
            await bot.edit_message_caption(chat_id=chat_id, message_id=message_id, caption=text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
    else:
        if photo:
            await bot.send_photo(chat_id, photo, caption=text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        else:
            await bot.send_message(chat_id, text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

async def check_subscription(user_id: int) -> bool:
    channels = db.get_required_channels()
    if not channels:
        return True
    for channel_id, channel_url, channel_name in channels:
        try:
            member = await bot.get_chat_member(channel_id, user_id)
            if member.status in ['left', 'kicked']:
                return False
        except:
            return False
    return True

def get_fee_display(fee: int) -> str:
    return "FREE" if fee == 0 else "PREMIUM"

def get_main_keyboard(user_id: int):
    coins = db.get_coins(user_id)
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Gates", callback_data="show_gates"),
         InlineKeyboardButton(text="Tools", callback_data="show_tools")],
        [InlineKeyboardButton(text="Programmers", callback_data="show_programmer"),
         InlineKeyboardButton(text=f"Coins {coins}", callback_data="show_coins")]
    ])

def back_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Back", callback_data="back_to_main")]
    ])

async def show_subscription_required(message: Message):
    channels = db.get_required_channels()
    text = " **Subscription Required**\n"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for channel_id, channel_url, channel_name in channels:
        keyboard.inline_keyboard.append([InlineKeyboardButton(text=f" ⦉   {channel_name}  ⦊ ", url=channel_url)])
    keyboard.inline_keyboard.append([InlineKeyboardButton(text="check", callback_data="check_sub")])
    await send_or_edit_with_image(message.chat.id, None, text, reply_markup=keyboard)

@dp.callback_query(lambda c: c.data == "check_sub")
async def check_sub_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    if await check_subscription(user_id):
        await callback.message.edit_text("✅ Subscription verified! You can now use the bot.", reply_markup=get_main_keyboard(user_id))
        await callback.answer("Verified")
    else:
        await callback.answer("You haven't joined all required channels yet.", show_alert=True)

@dp.message(Command("start"))
async def cmd_start(message: Message):
    user_id = message.from_user.id
    db.get_coins(user_id)
    if await check_subscription(user_id):
        await send_or_edit_with_image(message.chat.id, None, "Welcome! Choose an option:", reply_markup=get_main_keyboard(user_id))
    else:
        await show_subscription_required(message)

@dp.callback_query(lambda c: c.data == "show_gates")
async def show_gates(callback: CallbackQuery):
    text = "𝐀𝐕𝐀𝐈𝐋𝐀𝐁𝐋𝐄 𝐆𝐀𝐓𝐄𝐒:\n\n"
    for cmd, info in GATES.items():
        fee_display = get_fee_display(info["fee_single"])
        text += f"`/{cmd}` - {info['name']} ({fee_display})\n"
    await send_or_edit_with_image(callback.message.chat.id, callback.message.message_id, text, reply_markup=back_keyboard())
    await callback.answer()

@dp.callback_query(lambda c: c.data == "show_tools")
async def show_tools(callback: CallbackQuery):
    text = "ϟ 𝐓𝐎𝐎𝐋𝐒:\n/bin - Lookup BIN info\n/fakeus - Generate fake US address"
    await send_or_edit_with_image(callback.message.chat.id, callback.message.message_id, text, reply_markup=back_keyboard())
    await callback.answer()

@dp.callback_query(lambda c: c.data == "show_programmer")
async def show_programmer(callback: CallbackQuery):
    text = (
        f"ϟ **Programmers** ϟ\n\n"
        f"ϟ **Programmer  ⟶ ** [{DEV_NAME}]({DEV_LINK})\n"
        f"ϟ **Gater  ⟶ ** [{GATER_NAME}]({GATER_LINK})"
    )
    await send_or_edit_with_image(callback.message.chat.id, callback.message.message_id, text, reply_markup=back_keyboard())
    await callback.answer()

@dp.callback_query(lambda c: c.data == "show_coins")
async def show_coins(callback: CallbackQuery):
    user_id = callback.from_user.id
    coins = db.get_coins(user_id)
    text = f" **Your Coins:** `{coins}`\n\nEach scan costs 1 coin.\nAdmins are not charged."
    await send_or_edit_with_image(callback.message.chat.id, callback.message.message_id, text, reply_markup=back_keyboard())
    await callback.answer()

@dp.callback_query(lambda c: c.data == "back_to_main")
async def back_to_main(callback: CallbackQuery):
    user_id = callback.from_user.id
    await send_or_edit_with_image(callback.message.chat.id, callback.message.message_id, "Welcome back! Choose an option:", reply_markup=get_main_keyboard(user_id))
    await callback.answer()

@dp.message(Command("cancel"))
async def cancel_all(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id in scan_tasks:
        scan_tasks[user_id].cancel()
        del scan_tasks[user_id]
    await state.clear()
    await message.answer("✅ Cancelled all operations.")

def register_gate_commands():
    for cmd, info in GATES.items():
        @dp.message(Command(cmd))
        async def gate_command(message: Message, gate_cmd=cmd, module=info["module"], price=info["price"], gate_name=info["name"], fee_single=info["fee_single"]):
            user_id = message.from_user.id
            if not await check_subscription(user_id):
                await show_subscription_required(message)
                return
            if not db.is_admin(user_id):
                if not db.deduct_coins(user_id, fee_single):
                    await message.answer(f"❌ Insufficient coins. This gate requires {fee_single} coin(s) per single scan.")
                    return
            args = message.text.split(maxsplit=1)
            if len(args) < 2:
                await message.answer(f"Usage: /{gate_cmd} CC|MM|YYYY|CVV")
                return
            data_str = args[1]
            parts = data_str.split("|")
            if len(parts) != 4:
                await message.answer("Invalid format. Use: CC|MM|YYYY|CVV")
                return
            cc, month, year, cvv = parts
            bin_num = cc[:6] if cc[:6].isdigit() else "000000"
            bin_info, bank, country = await get_bin_info(bin_num)

            card_data = {"cc": cc, "month": month, "year": year, "cvv": cvv}
            try:
                result = await module.check_single(card_data)
                checked_by = message.from_user.first_name or message.from_user.username or str(message.from_user.id)
                msg = (
                    f"- - - - - - - - - - - - - - - - - - - - - - -\n"
                    f"[ϟ] 𝐂𝐚𝐫𝐝: `{cc}|{month}|{year}|{cvv}`\n"
                    f"[ϟ] 𝐒𝐭𝐚𝐭𝐮𝐬: {result['status']}\n"
                    f"[ϟ] 𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞: {result['response']}\n"
                    f"- - - - - - - - - - - - - - - - - - - - - - -\n"
                    f"[ϟ] 𝐁𝐢𝐧: {bin_info}\n"
                    f"[ϟ] 𝐁𝐚𝐧𝐤: {bank}\n"
                    f"[ϟ] 𝐂𝐨𝐮𝐧𝐭𝐫𝐲: {country}\n"
                    f"- - - - - - - - - - - - - - - - - - - - - - -\n"
                    f"[ϟ] T/t : {result['took']}s \n"
                    f"[⌥]  𝐆𝐚𝐭𝐞𝐰𝐚𝐲: {gate_name}\n"
                    f"[⌥]  𝐂𝐡𝐞𝐜𝐤𝐞𝐝 𝐛𝐲: {checked_by}\n"
                    f"[⌥]  𝐆𝐚𝐭𝐞 𝐏𝐫𝐢𝐜𝐞: {price}\n"
                    f"- - - - - - - - - - - - - - - - - - - - - - -\n"
                    f"[⌤] 𝐃𝐞𝐯 𝐛𝐲: [{DEV_NAME}]({DEV_LINK})"
                )
                await message.answer(msg, parse_mode=ParseMode.MARKDOWN)
            except Exception as e:
                await message.answer(f"⚠️ Error: {str(e)}")

register_gate_commands()

@dp.message(F.document)
async def handle_txt_file(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if not await check_subscription(user_id):
        await show_subscription_required(message)
        return
    if await state.get_state() is not None:
        return
    doc = message.document
    if not doc.file_name.endswith('.txt'):
        await message.answer("Only .txt files are allowed.")
        return

    file_id = doc.file_id
    file_name = doc.file_name
    file = await bot.get_file(file_id)
    file_bytes = await bot.download_file(file.file_path)
    content = file_bytes.read().decode("utf-8", errors="ignore")
    lines = content.strip().splitlines()
    valid_cards = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        parts_line = line.split("|")
        if len(parts_line) == 4:
            valid_cards.append(parts_line)
    if not valid_cards:
        await message.answer("❌ No valid card lines found.")
        return
    if not GATES:
        await message.answer("No gates available.")
        return

    token = secrets.token_hex(4)
    temp_storage[token] = {
        "file_id": file_id,
        "file_name": file_name,
        "user_id": user_id,
        "total_cards": len(valid_cards)
    }
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for cmd, info in GATES.items():
        fee_display = get_fee_display(info["fee_bulk"])
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text=f"{info['name']} ({fee_display})", callback_data=f"bulk_{cmd}:{token}")
        ])
    keyboard.inline_keyboard.append([InlineKeyboardButton(text="❌ Cancel", callback_data="cancel_bulk")])
    await message.answer(
        f"📁 File received: `{file_name}`\nTotal cards: {len(valid_cards)}\nChoose a gate to scan all cards:\n(PREMIUM gates deduct coins per card during scan)",
        reply_markup=keyboard,
        parse_mode=ParseMode.MARKDOWN
    )

@dp.callback_query(lambda c: c.data == "cancel_bulk")
async def cancel_bulk_before_start(callback: CallbackQuery):
    await callback.message.edit_text("❌ Bulk scan cancelled.")
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith("bulk_") and ":" in c.data and not c.data.startswith("bulk_cancel_scan"))
async def start_bulk_scan(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    if not await check_subscription(user_id):
        await callback.answer("Please subscribe to required channels first.", show_alert=True)
        return
    parts = callback.data.split(":")
    if len(parts) != 2:
        await callback.message.edit_text("❌ Invalid format. Please upload the file again.")
        await callback.answer()
        return
    cmd_token = parts[0].replace("bulk_", "")
    token = parts[1]
    if token not in temp_storage:
        await callback.message.edit_text("❌ Session expired. Please send the .txt file again.")
        await callback.answer()
        return
    file_data = temp_storage[token]
    file_id = file_data["file_id"]
    file_name = file_data["file_name"]
    original_user_id = file_data["user_id"]
    if original_user_id != user_id:
        await callback.message.edit_text("❌ This file was uploaded by another user.")
        await callback.answer()
        return

    del temp_storage[token]

    if cmd_token not in GATES:
        await callback.message.edit_text("❌ Unknown gate.")
        await callback.answer()
        return

    gate_info = GATES[cmd_token]
    module = gate_info["module"]
    price = gate_info["price"]
    gate_name = gate_info["name"]
    delay = gate_info["delay"]
    fee_bulk = gate_info["fee_bulk"]

    file = await bot.get_file(file_id)
    file_bytes = await bot.download_file(file.file_path)
    content = file_bytes.read().decode("utf-8", errors="ignore")
    lines = content.strip().splitlines()
    cards: List[Tuple[str, str, str, str]] = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        parts_line = line.split("|")
        if len(parts_line) != 4:
            continue
        cc, month, year, cvv = parts_line
        cards.append((cc, month, year, cvv))
    if not cards:
        await callback.message.edit_text("⚠️ No valid card lines found.")
        return

    total = len(cards)
    approved = 0
    declined = 0
    current_index = 0

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Card: Loading...", callback_data="bulk_show_cc")],
        [InlineKeyboardButton(text="💬 Resp: ...", callback_data="bulk_show_response")],
        [InlineKeyboardButton(text="✅ 𝐀𝐏𝐏𝐑𝐎𝐕𝐄𝐃: 0", callback_data="bulk_show_approved")],
        [InlineKeyboardButton(text="❌ 𝐃𝐄𝐂𝐋𝐈𝐍𝐄𝐃: 0", callback_data="bulk_show_declined")],
        [InlineKeyboardButton(text=f"𝐑𝐄𝐌𝐀𝐈𝐍𝐈𝐍𝐆: {total}", callback_data="bulk_show_remaining")],
        [InlineKeyboardButton(text=f"𝐓𝐎𝐓𝐀𝐋: {total}", callback_data="bulk_show_total")],
        [InlineKeyboardButton(text="🚫 𝐂𝐀𝐍𝐂𝐄𝐋", callback_data="bulk_cancel_scan")]
    ])

    await callback.message.edit_text(
        "🔄 **Bulk Scan Started**\n*Buttons update automatically.*\nCoins deducted per card during scan.",
        reply_markup=keyboard,
        parse_mode=ParseMode.MARKDOWN
    )
    await callback.answer()

    await state.set_state(BulkScanState.scanning)
    await state.update_data(
        cards=cards,
        current_index=current_index,
        approved=approved,
        declined=declined,
        total=total,
        module=module,
        gate_name=gate_name,
        price=price,
        delay=delay,
        gate_cmd=cmd_token,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        file_id=file_id,
        approved_texts=[],
        last_card="",
        last_response="",
        user_id=user_id,
        fee_bulk=fee_bulk
    )

    if user_id in scan_tasks:
        scan_tasks[user_id].cancel()
    task = asyncio.create_task(process_next_card(user_id, state))
    scan_tasks[user_id] = task

async def process_next_card(user_id: int, state: FSMContext):
    try:
        while True:
            data = await state.get_data()
            cards: List[Tuple[str, str, str, str]] = data.get("cards", [])
            current_index = data.get("current_index", 0)
            approved = data.get("approved", 0)
            declined = data.get("declined", 0)
            total = data.get("total", 0)
            module = data.get("module")
            gate_name = data.get("gate_name")
            price = data.get("price")
            delay = data.get("delay", 1.0)
            message_id = data.get("message_id")
            file_id = data.get("file_id")
            approved_texts: List[str] = data.get("approved_texts", [])
            fee_bulk = data.get("fee_bulk", 1)

            if "checked_by" not in data:
                user = await bot.get_chat(data.get("chat_id"))
                checked_by = user.first_name or user.username or str(user.id)
                await state.update_data(checked_by=checked_by)
            else:
                checked_by = data["checked_by"]

            if current_index >= len(cards):
                final_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="✅ Done", callback_data="bulk_close")]
                ])
                final_text = (
                    f"✅ **Bulk scan finished**\n"
                    f"Approved: {approved}\nDeclined: {declined}\nTotal: {total}"
                )
                await bot.edit_message_text(
                    final_text,
                    chat_id=data.get("chat_id"),
                    message_id=message_id,
                    reply_markup=final_keyboard,
                    parse_mode=ParseMode.MARKDOWN
                )
                if approved_texts:
                    approved_content = "\n".join(approved_texts)
                    file_bytes = approved_content.encode("utf-8")
                    input_file = BufferedInputFile(file_bytes, filename="approved_cards.txt")
                    await bot.send_document(data.get("chat_id"), document=input_file, caption=f"✅ Approved cards ({approved})")
                try:
                    await bot.delete_file(file_id)
                except:
                    pass
                await state.clear()
                if user_id in scan_tasks:
                    del scan_tasks[user_id]
                return

            # الفحص الجماعي: خصم عملة واحدة لكل بطاقة أثناء التقدم (إذا كانت البوابة PREMIUM و fee_bulk > 0)
            if not db.is_admin(user_id) and fee_bulk > 0:
                coins = db.get_coins(user_id)
                if coins < fee_bulk:
                    # توقف الفحص بسبب نقص العملات، نرسل النتائج الحالية وننهي
                    final_text = (
                        f"❌ **Scan stopped due to insufficient coins**\n"
                        f"Approved: {approved}\nDeclined: {declined}\nTotal processed: {current_index}\n"
                        f"Remaining cards in file: {total - current_index}\n"
                        f"Coins left: {coins}"
                    )
                    final_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="Close", callback_data="bulk_close")]
                    ])
                    await bot.edit_message_text(
                        final_text,
                        chat_id=data.get("chat_id"),
                        message_id=message_id,
                        reply_markup=final_keyboard,
                        parse_mode=ParseMode.MARKDOWN
                    )
                    # إرسال ملف البطاقات المقبولة حتى الآن إن وجد
                    if approved_texts:
                        approved_content = "\n".join(approved_texts)
                        file_bytes = approved_content.encode("utf-8")
                        input_file = BufferedInputFile(file_bytes, filename="approved_cards.txt")
                        await bot.send_document(data.get("chat_id"), document=input_file, caption=f"✅ Approved cards ({approved})")
                    try:
                        await bot.delete_file(file_id)
                    except:
                        pass
                    await state.clear()
                    if user_id in scan_tasks:
                        del scan_tasks[user_id]
                    return
                # خصم العملات
                db.remove_coins(user_id, fee_bulk)

            cc, month, year, cvv = cards[current_index]
            bin_num = cc[:6] if cc[:6].isdigit() else "000000"
            bin_info, bank, country = await get_bin_info(bin_num)
            card_data = {"cc": cc, "month": month, "year": year, "cvv": cvv}
            try:
                result = await module.check_single(card_data)
                is_approved = result['status'].lower() == "approved"
                current_card_display = f"{cc}|{month}|{year}|{cvv}"
                response_display = f"{result['status']} - {result['response']}"
                if is_approved:
                    approved += 1
                    msg_text = (
                        f"- - - - - - - - - - - - - - - - - - - - - - -\n"
                        f"[ϟ] 𝐂𝐚𝐫𝐝: `{cc}|{month}|{year}|{cvv}`\n"
                        f"[ϟ] 𝐒𝐭𝐚𝐭𝐮𝐬: {result['status']}\n"
                        f"[ϟ] 𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞: {result['response']}\n"
                        f"- - - - - - - - - - - - - - - - - - - - - - -\n"
                        f"[ϟ] 𝐁𝐢𝐧: {bin_info}\n"
                        f"[ϟ] 𝐁𝐚𝐧𝐤: {bank}\n"
                        f"[ϟ] 𝐂𝐨𝐮𝐧𝐭𝐫𝐲: {country}\n"
                        f"- - - - - - - - - - - - - - - - - - - - - - -\n"
                        f"[ϟ] T/t : {result['took']}s \n"
                        f"[⌥]  𝐆𝐚𝐭𝐞𝐰𝐚𝐲: {gate_name}\n"
                        f"[⌥]  𝐂𝐡𝐞𝐜𝐤𝐞𝐝 𝐛𝐲: {checked_by}\n"
                        f"[⌥]  𝐆𝐚𝐭𝐞 𝐏𝐫𝐢𝐜𝐞: {price}\n"
                        f"- - - - - - - - - - - - - - - - - - - - - - -\n"
                        f"[⌤] 𝐃𝐞𝐯 𝐛𝐲: [{DEV_NAME}]({DEV_LINK})"
                    )
                    await bot.send_message(data.get("chat_id"), msg_text, parse_mode=ParseMode.MARKDOWN)
                    approved_texts.append(f"{cc}|{month}|{year}|{cvv}")
                else:
                    declined += 1
                await state.update_data(
                    current_index=current_index + 1,
                    approved=approved,
                    declined=declined,
                    approved_texts=approved_texts,
                    last_card=current_card_display,
                    last_response=response_display
                )
                remaining_cards = total - (current_index + 1)
                updated_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text=f"{current_card_display[:30]}", callback_data="bulk_show_cc")],
                    [InlineKeyboardButton(text=f"{response_display[:35]}", callback_data="bulk_show_response")],
                    [InlineKeyboardButton(text=f"✅ 𝐀𝐏𝐏𝐑𝐎𝐕𝐄𝐃: {approved}", callback_data="bulk_show_approved")],
                    [InlineKeyboardButton(text=f"❌ 𝐃𝐄𝐂𝐋𝐈𝐍𝐄𝐃: {declined}", callback_data="bulk_show_declined")],
                    [InlineKeyboardButton(text=f"📊 𝐑𝐄𝐌𝐀𝐈𝐍𝐈𝐍𝐆: {remaining_cards}", callback_data="bulk_show_remaining")],
                    [InlineKeyboardButton(text=f"🔢 𝐓𝐎𝐓𝐀𝐋: {total}", callback_data="bulk_show_total")],
                    [InlineKeyboardButton(text="🚫 𝐂𝐀𝐍𝐂𝐄𝐋", callback_data="bulk_cancel_scan")]
                ])
                await bot.edit_message_reply_markup(chat_id=data.get("chat_id"), message_id=message_id, reply_markup=updated_keyboard)
                await asyncio.sleep(delay)
            except Exception as e:
                declined += 1
                await state.update_data(
                    current_index=current_index + 1,
                    declined=declined,
                    approved_texts=approved_texts
                )
    except asyncio.CancelledError:
        data = await state.get_data()
        file_id = data.get("file_id")
        if file_id:
            try:
                await bot.delete_file(file_id)
            except:
                pass
        await state.clear()
        if user_id in scan_tasks:
            del scan_tasks[user_id]
        chat_id = data.get("chat_id")
        if chat_id:
            await bot.send_message(chat_id, "❌ Scan cancelled.")
        return

@dp.callback_query(BulkScanState.scanning, lambda c: c.data.startswith("bulk_show_"))
async def bulk_show_info(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if not data:
        await callback.answer("Scan not active.", show_alert=True)
        return
    action = callback.data.split("_")[-1]
    if action == "cc":
        card = data.get("last_card", "No card yet")
        await callback.answer(f"Full Card: {card}", show_alert=True)
    elif action == "response":
        resp = data.get("last_response", "No response yet")
        await callback.answer(resp, show_alert=True)
    elif action == "approved":
        await callback.answer(f"Approved: {data.get('approved', 0)}", show_alert=True)
    elif action == "declined":
        await callback.answer(f"Declined: {data.get('declined', 0)}", show_alert=True)
    elif action == "remaining":
        total = data.get("total", 0)
        current = data.get("current_index", 0)
        remain = total - current
        await callback.answer(f"Remaining: {remain}", show_alert=True)
    elif action == "total":
        await callback.answer(f"Total: {data.get('total', 0)}", show_alert=True)
    await callback.answer()

@dp.callback_query(BulkScanState.scanning, lambda c: c.data == "bulk_cancel_scan")
async def bulk_cancel_scan(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    if user_id in scan_tasks:
        scan_tasks[user_id].cancel()
        del scan_tasks[user_id]
    data = await state.get_data()
    file_id = data.get("file_id")
    if file_id:
        try:
            await bot.delete_file(file_id)
        except:
            pass
    await state.clear()
    await callback.message.edit_text("❌ Scan cancelled.", reply_markup=None)
    await callback.answer()

@dp.callback_query(lambda c: c.data == "bulk_close")
async def bulk_close(callback: CallbackQuery):
    await callback.message.delete()
    await callback.answer()

def include_tools():
    tools_dir = Path("tools")
    if not tools_dir.exists():
        return
    for file in tools_dir.glob("*.py"):
        if file.name == "__init__.py":
            continue
        try:
            module = importlib.import_module(f"tools.{file.stem}")
            if hasattr(module, "router"):
                dp.include_router(module.router)
        except Exception as e:
            print(f"Error importing tool {file.stem}: {e}")

include_tools()
dp.include_router(admin_router)

async def main():
    print("Bot is running...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())