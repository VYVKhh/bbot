from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm import state, context
from aiogram.types import Message, CallbackQuery
import database as db

router = Router()

class AddAdminState(state.StatesGroup):
    waiting_user_id = state.State()

class RemoveAdminState(state.StatesGroup):
    waiting_user_id = state.State()

class BanUserState(state.StatesGroup):
    waiting_user_id = state.State()

class UnbanUserState(state.StatesGroup):
    waiting_user_id = state.State()

class AddUserState(state.StatesGroup):
    waiting_user_id = state.State()

class BroadcastState(state.StatesGroup):
    waiting_message = state.State()

class AddCoinsState(state.StatesGroup):
    waiting_user_id = state.State()
    waiting_amount = state.State()

class RemoveCoinsState(state.StatesGroup):
    waiting_user_id = state.State()
    waiting_amount = state.State()

class AddChannelState(state.StatesGroup):
    waiting_channel_id = state.State()
    waiting_channel_url = state.State()
    waiting_channel_name = state.State()

class RemoveChannelState(state.StatesGroup):
    waiting_channel_id = state.State()

class SetProgrammerState(state.StatesGroup):
    waiting_text = state.State()

def is_admin(func):
    async def wrapper(message_or_callback, *args, **kwargs):
        user_id = None
        if isinstance(message_or_callback, Message):
            user_id = message_or_callback.from_user.id
        elif isinstance(message_or_callback, CallbackQuery):
            user_id = message_or_callback.from_user.id
        if not db.is_admin(user_id):
            if isinstance(message_or_callback, Message):
                await message_or_callback.answer("⛔ You are not an admin.")
            else:
                await message_or_callback.answer("⛔ You are not an admin.", show_alert=True)
            return
        return await func(message_or_callback, *args, **kwargs)
    return wrapper

def admin_menu_keyboard():
    return types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="➕ Add Admin", callback_data="admin_add_admin"),
         types.InlineKeyboardButton(text="➖ Remove Admin", callback_data="admin_remove_admin")],
        [types.InlineKeyboardButton(text="🚫 Ban User", callback_data="admin_ban_user"),
         types.InlineKeyboardButton(text="✅ Unban User", callback_data="admin_unban_user")],
        [types.InlineKeyboardButton(text="👤 Add User", callback_data="admin_add_user"),
         types.InlineKeyboardButton(text="📊 Stats", callback_data="admin_stats")],
        [types.InlineKeyboardButton(text="📢 Broadcast", callback_data="admin_broadcast")],
        [types.InlineKeyboardButton(text="💰 Add Coins", callback_data="admin_add_coins"),
         types.InlineKeyboardButton(text="💸 Remove Coins", callback_data="admin_remove_coins")],
        [types.InlineKeyboardButton(text="🔄 Reset All Coins", callback_data="admin_reset_coins")],
        [types.InlineKeyboardButton(text="📢 Add Channel", callback_data="admin_add_channel"),
         types.InlineKeyboardButton(text="🗑️ Remove Channel", callback_data="admin_remove_channel")],
        [types.InlineKeyboardButton(text="✏️ Set Programmer Text", callback_data="admin_set_programmer")],
        [types.InlineKeyboardButton(text="🔙 Back", callback_data="back_to_main")]
    ])

@router.message(Command("admin"))
@is_admin
async def admin_panel(message: Message, **kwargs):
    await message.answer("🛠️ **Admin Panel**\nChoose an action:", reply_markup=admin_menu_keyboard(), parse_mode="Markdown")

@router.callback_query(lambda c: c.data.startswith("admin_"))
@is_admin
async def admin_actions(callback: CallbackQuery, state: context.FSMContext, **kwargs):
    action = callback.data.split("_", 1)[1]
    if action == "add_admin":
        await callback.message.edit_text("Send the user ID to add as admin.")
        await state.set_state(AddAdminState.waiting_user_id)
    elif action == "remove_admin":
        await callback.message.edit_text("Send the user ID to remove from admins.")
        await state.set_state(RemoveAdminState.waiting_user_id)
    elif action == "ban_user":
        await callback.message.edit_text("Send the user ID to ban.")
        await state.set_state(BanUserState.waiting_user_id)
    elif action == "unban_user":
        await callback.message.edit_text("Send the user ID to unban.")
        await state.set_state(UnbanUserState.waiting_user_id)
    elif action == "add_user":
        await callback.message.edit_text("Send the user ID to add to database.")
        await state.set_state(AddUserState.waiting_user_id)
    elif action == "stats":
        await callback.message.edit_text("Fetching stats...")
        await send_stats(callback)
    elif action == "broadcast":
        await callback.message.edit_text("Send the message to broadcast.")
        await state.set_state(BroadcastState.waiting_message)
    elif action == "add_coins":
        await callback.message.edit_text("Send the user ID to add coins.")
        await state.set_state(AddCoinsState.waiting_user_id)
    elif action == "remove_coins":
        await callback.message.edit_text("Send the user ID to remove coins.")
        await state.set_state(RemoveCoinsState.waiting_user_id)
    elif action == "reset_coins":
        await reset_coins_all(callback)
    elif action == "add_channel":
        await callback.message.edit_text("Send the channel ID (e.g., -100123456 or @channel), then URL, then name each in a new message.")
        await state.set_state(AddChannelState.waiting_channel_id)
    elif action == "remove_channel":
        await callback.message.edit_text("Send the channel ID to remove from required subscription.")
        await state.set_state(RemoveChannelState.waiting_channel_id)
    elif action == "set_programmer":
        await callback.message.edit_text("Send the new text for Programmers section (supports Markdown).")
        await state.set_state(SetProgrammerState.waiting_text)
    await callback.answer()

async def send_stats(callback: CallbackQuery):
    users = db.get_all_users()
    admins = db.get_all_admins()
    banned = [uid for uid in users if db.is_banned(uid)]
    total_coins = sum(db.get_coins(uid) for uid in users)
    msg = (
        f"📊 **Bot Statistics**\n"
        f"👥 Total users: {len(users)}\n"
        f"👑 Admins: {len(admins)}\n"
        f"🚫 Banned: {len(banned)}\n"
        f"💰 Total coins: {total_coins}"
    )
    await callback.message.edit_text(msg, parse_mode="Markdown", reply_markup=admin_menu_keyboard())

async def reset_coins_all(callback: CallbackQuery):
    users = db.get_all_users()
    for uid in users:
        db.set_coins(uid, 0)
    msg = "✅ All coins reset to 0."
    await callback.message.edit_text(msg, reply_markup=admin_menu_keyboard())

@router.message(AddAdminState.waiting_user_id)
@is_admin
async def process_add_admin(message: Message, state: context.FSMContext, **kwargs):
    try:
        user_id = int(message.text.strip())
        db.add_admin(user_id)
        await message.answer(f"✅ Admin {user_id} added.", reply_markup=admin_menu_keyboard())
    except:
        await message.answer("Invalid user ID.", reply_markup=admin_menu_keyboard())
    await state.clear()

@router.message(RemoveAdminState.waiting_user_id)
@is_admin
async def process_remove_admin(message: Message, state: context.FSMContext, **kwargs):
    try:
        user_id = int(message.text.strip())
        db.remove_admin(user_id)
        await message.answer(f"✅ Admin {user_id} removed.", reply_markup=admin_menu_keyboard())
    except:
        await message.answer("Invalid user ID.", reply_markup=admin_menu_keyboard())
    await state.clear()

@router.message(BanUserState.waiting_user_id)
@is_admin
async def process_ban_user(message: Message, state: context.FSMContext, **kwargs):
    try:
        user_id = int(message.text.strip())
        db.ban_user(user_id)
        await message.answer(f"✅ User {user_id} banned.", reply_markup=admin_menu_keyboard())
    except:
        await message.answer("Invalid user ID.", reply_markup=admin_menu_keyboard())
    await state.clear()

@router.message(UnbanUserState.waiting_user_id)
@is_admin
async def process_unban_user(message: Message, state: context.FSMContext, **kwargs):
    try:
        user_id = int(message.text.strip())
        db.unban_user(user_id)
        await message.answer(f"✅ User {user_id} unbanned.", reply_markup=admin_menu_keyboard())
    except:
        await message.answer("Invalid user ID.", reply_markup=admin_menu_keyboard())
    await state.clear()

@router.message(AddUserState.waiting_user_id)
@is_admin
async def process_add_user(message: Message, state: context.FSMContext, **kwargs):
    try:
        user_id = int(message.text.strip())
        db.get_coins(user_id)
        await message.answer(f"✅ User {user_id} added to system.", reply_markup=admin_menu_keyboard())
    except:
        await message.answer("Invalid user ID.", reply_markup=admin_menu_keyboard())
    await state.clear()

@router.message(BroadcastState.waiting_message)
@is_admin
async def process_broadcast(message: Message, state: context.FSMContext, **kwargs):
    text = message.text
    users = db.get_all_users()
    sent = 0
    for uid in users:
        try:
            await message.bot.send_message(uid, text)
            sent += 1
        except:
            pass
    await message.answer(f"✅ Broadcast sent to {sent} users.", reply_markup=admin_menu_keyboard())
    await state.clear()

@router.message(AddCoinsState.waiting_user_id)
@is_admin
async def process_add_coins_user_id(message: Message, state: context.FSMContext, **kwargs):
    try:
        user_id = int(message.text.strip())
        await state.update_data(user_id=user_id)
        await message.answer("Send the amount of coins to add.")
        await state.set_state(AddCoinsState.waiting_amount)
    except:
        await message.answer("Invalid user ID. Start over with /admin.")
        await state.clear()

@router.message(AddCoinsState.waiting_amount)
@is_admin
async def process_add_coins_amount(message: Message, state: context.FSMContext, **kwargs):
    try:
        amount = int(message.text.strip())
        data = await state.get_data()
        user_id = data.get("user_id")
        db.add_coins(user_id, amount)
        await message.answer(f"✅ Added {amount} coins to {user_id}.", reply_markup=admin_menu_keyboard())
    except:
        await message.answer("Invalid amount.", reply_markup=admin_menu_keyboard())
    await state.clear()

@router.message(RemoveCoinsState.waiting_user_id)
@is_admin
async def process_remove_coins_user_id(message: Message, state: context.FSMContext, **kwargs):
    try:
        user_id = int(message.text.strip())
        await state.update_data(user_id=user_id)
        await message.answer("Send the amount of coins to remove.")
        await state.set_state(RemoveCoinsState.waiting_amount)
    except:
        await message.answer("Invalid user ID. Start over with /admin.")
        await state.clear()

@router.message(RemoveCoinsState.waiting_amount)
@is_admin
async def process_remove_coins_amount(message: Message, state: context.FSMContext, **kwargs):
    try:
        amount = int(message.text.strip())
        data = await state.get_data()
        user_id = data.get("user_id")
        db.remove_coins(user_id, amount)
        await message.answer(f"✅ Removed {amount} coins from {user_id}.", reply_markup=admin_menu_keyboard())
    except:
        await message.answer("Invalid amount.", reply_markup=admin_menu_keyboard())
    await state.clear()

@router.message(AddChannelState.waiting_channel_id)
@is_admin
async def process_add_channel_id(message: Message, state: context.FSMContext, **kwargs):
    channel_id = message.text.strip()
    await state.update_data(channel_id=channel_id)
    await message.answer("Now send the channel URL (e.g., https://t.me/username).")
    await state.set_state(AddChannelState.waiting_channel_url)

@router.message(AddChannelState.waiting_channel_url)
@is_admin
async def process_add_channel_url(message: Message, state: context.FSMContext, **kwargs):
    channel_url = message.text.strip()
    await state.update_data(channel_url=channel_url)
    await message.answer("Now send the channel display name.")
    await state.set_state(AddChannelState.waiting_channel_name)

@router.message(AddChannelState.waiting_channel_name)
@is_admin
async def process_add_channel_name(message: Message, state: context.FSMContext, **kwargs):
    channel_name = message.text.strip()
    data = await state.get_data()
    db.add_required_channel(data["channel_id"], data["channel_url"], channel_name)
    await message.answer(f"✅ Channel {channel_name} added.", reply_markup=admin_menu_keyboard())
    await state.clear()

@router.message(RemoveChannelState.waiting_channel_id)
@is_admin
async def process_remove_channel(message: Message, state: context.FSMContext, **kwargs):
    channel_id = message.text.strip()
    db.remove_required_channel(channel_id)
    await message.answer("✅ Channel removed.", reply_markup=admin_menu_keyboard())
    await state.clear()

@router.message(SetProgrammerState.waiting_text)
@is_admin
async def process_set_programmer(message: Message, state: context.FSMContext, **kwargs):
    new_text = message.text
    db.set_programmer_text(new_text)
    await message.answer("✅ Programmer text updated.", reply_markup=admin_menu_keyboard())
    await state.clear()