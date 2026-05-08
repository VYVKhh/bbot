import random
from aiogram import Router, types
from aiogram.filters import Command

router = Router()

# بيانات مترابطة: الولاية -> قائمة (المدن، الرموز البريدية)
state_data = {
    "Texas": {
        "cities": ["Houston", "Dallas", "Austin", "San Antonio"],
        "zip_codes": ["77056", "75201", "78701", "78205"]
    },
    "California": {
        "cities": ["Los Angeles", "San Diego", "San Francisco", "Sacramento"],
        "zip_codes": ["90210", "92101", "94102", "94203"]
    },
    "Illinois": {
        "cities": ["Chicago", "Springfield", "Naperville", "Aurora"],
        "zip_codes": ["60601", "62701", "60540", "60505"]
    },
    "Arizona": {
        "cities": ["Phoenix", "Tucson", "Mesa", "Scottsdale"],
        "zip_codes": ["85001", "85701", "85201", "85251"]
    },
    "Pennsylvania": {
        "cities": ["Philadelphia", "Pittsburgh", "Allentown", "Erie"],
        "zip_codes": ["19107", "15201", "18101", "16501"]
    },
    "Florida": {
        "cities": ["Miami", "Orlando", "Tampa", "Jacksonville"],
        "zip_codes": ["33101", "32801", "33601", "32202"]
    },
    "Ohio": {
        "cities": ["Columbus", "Cleveland", "Cincinnati", "Toledo"],
        "zip_codes": ["43215", "44101", "45201", "43601"]
    },
    "Michigan": {
        "cities": ["Detroit", "Grand Rapids", "Warren", "Sterling Heights"],
        "zip_codes": ["48201", "49501", "48089", "48310"]
    },
    "Georgia": {
        "cities": ["Atlanta", "Augusta", "Columbus", "Savannah"],
        "zip_codes": ["30301", "30901", "31901", "31401"]
    },
    "North Carolina": {
        "cities": ["Charlotte", "Raleigh", "Greensboro", "Durham"],
        "zip_codes": ["28201", "27601", "27401", "27701"]
    }
}

first_names = ["James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda", "William", "Elizabeth"]
last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]
streets = ["Main St", "Oak Avenue", "Maple Drive", "Cedar Road", "Elm Street", "Pine Lane", "Washington Blvd", "Lake Shore Dr"]
email_domains = ["gmail.com", "yahoo.com", "outlook.com", "protonmail.com", "icloud.com"]

def generate_phone():
    return f"+1{random.randint(200,999)}{random.randint(1000000,9999999)}"

def generate_email(first, last):
    username = f"{first.lower()}.{last.lower()}{random.randint(1,999)}"
    return f"{username}@{random.choice(email_domains)}"

def generate_dob():
    year = random.randint(1970, 2005)
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    return f"{month:02d}/{day:02d}/{year}"

def generate_ssn():
    return f"{random.randint(100,999)}-{random.randint(10,99)}-{random.randint(1000,9999)}"

@router.message(Command("fakeus"))
async def fake_us(message: types.Message):
    first = random.choice(first_names)
    last = random.choice(last_names)
    full_name = f"{first} {last}"
    
    # اختيار ولاية عشوائية ثم مدينة ورمز بريدي متوافقين
    state = random.choice(list(state_data.keys()))
    city = random.choice(state_data[state]["cities"])
    zip_code = random.choice(state_data[state]["zip_codes"])
    street_num = random.randint(100, 9999)
    street = random.choice(streets)
    
    email = generate_email(first, last)
    phone = generate_phone()
    dob = generate_dob()
    ssn = generate_ssn()
    
    text = (
        f"🇺🇸 **Fake US Identity**\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 **Name:** {full_name}\n"
        f"🎂 **DOB:** {dob}\n"
        f"🔢 **SSN:** `{ssn}`\n"
        f"📧 **Email:** `{email}`\n"
        f"📞 **Phone:** `{phone}`\n"
        f"🏠 **Address:** {street_num} {street}\n"
        f"🏙️ **City:** {city}\n"
        f"🗺️ **State:** {state}\n"
        f"📮 **ZIP:** {zip_code}\n"
        f"🌎 **Country:** United States\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )
    await message.answer(text, parse_mode="Markdown")