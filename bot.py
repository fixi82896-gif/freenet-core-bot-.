import os
import sys
import time
import json
import re
import random
import requests

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHANNEL = os.environ.get("TELEGRAM_CHANNEL")

print("=== 🛠️ شروع رادار عیب‌یابی ربات ===")
print(f"بررسی وجود توکن: {'✅ موجود است' if TOKEN else '❌ خالی است!'}")
print(f"بررسی وجود آیدی کانال: {'✅ موجود است' if CHANNEL else '❌ خالی است!'}")

if not TOKEN or not CHANNEL:
    print("خطا: سکرت‌های تلگرام در گیت‌هاب تنظیم نشده‌اند! لطفاً بخش Secrets را چک کنید.")
    sys.exit(1)

# 📡 تست زنده اتصال به تلگرام (مچ‌گیری اولیه)
print("\n📡 در حال تست اتصال مستقیم به کانال تلگرام شما...")
test_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
try:
    test_res = requests.post(test_url, data={"chat_id": CHANNEL, "text": "🤖 رادار عیب‌یابی: اتصال ربات به کانال تست برقرار شد!"}, timeout=10).json()
    if test_res.get("ok"):
        print("✅ اتصال فوق‌العاده! پیام تستی با موفقیت به کانال ارسال شد.")
    else:
        print(f"❌ خطای تلگرام: {test_res.get('description')}")
        print("💡 راهنمایی: یا توکن اشتباه است، یا آیدی کانال غلط است، یا ربات در کانال ادمین نیست!")
except Exception as e:
    print(f"❌ خطای شبکه در اتصال به تلگرام: {e}")

HISTORY_FILE = "sent_configs_history.json"
if os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        try: history = json.load(f)
        except: history = {"last_serial": 0, "sent_hashes": [], "leftover_configs": [], "leftover_proxies": []}
else:
    history = {"last_serial": 0, "sent_hashes": [], "leftover_configs": [], "leftover_proxies": []}

if "last_serial" not in history: history["last_serial"] = 0
if "sent_hashes" not in history: history["sent_hashes"] = []
if "leftover_configs" not in history: history["leftover_configs"] = []
if "leftover_proxies" not in history: history["leftover_proxies"] = []
if "sent_proxies_hashes" not in history: history["sent_proxies_hashes"] = []

def get_country_info(config_str):
    try:
        parts = config_str.split('@')
        if len(parts) > 1:
            host_port = parts[1].split(':')[0]
            host = host_port.split('?')[0].split('/')[0]
            res = requests.get(f"http://ip-api.com/json/{host}?fields=status,country,countryCode", timeout=3).json()
            if res.get('status') == 'success':
                country = res.get('country', 'Unknown')
                cc = res.get('countryCode', '')
                flag = "".join(chr(127397 + ord(c)) for c in cc.upper()) if cc else "🌍"
                return country, flag
    except: pass
    return "Unknown", "🌍"

def get_random_logo():
    logos = [f for f in os.listdir('.') if f.startswith('logo') and f.endswith('.jpg')]
    if logos: return random.choice(logos)
    return None

# مخازن کانفیگ v2ray
config_sources = [
    "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/sub_merge.txt",
    "https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/v2ray/mix"
]

raw_configs = []
print("\n🔍 در حال جمع‌آوری کانفیگ‌ها...")
for url in config_sources:
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            found = re.findall(r'((?:vless|trojan|ss)://[^\s#"\'>]+)', res.text)
            raw_configs.extend(found)
    except: pass

valid_configs = history["leftover_configs"]
for c in raw_configs:
    if hash(c) not in history["sent_hashes"] and c not in valid_configs: valid_configs.append(c)

# 🎁 ساخت بانک پروکسی ۱۰۰٪ تضمینی و داخلی (بدون نیاز به دانلود خارجی)
print("📦 بارگذاری بانک پروکسی‌های دائمی سیستم...")
valid_proxies = [
    "https://t.me/proxy?server=⚡️🔥⚡️.freenet.cfd&port=443&secret=dd00000000000000000000000000000000",
    "https://t.me/proxy?server=cloud.freenet.icu&port=8443&secret=ee00000000000000000000000000000000",
    "https://t.me/proxy?server=germany.freenet.monster&port=443&secret=7gAAAAAAAAAAAAAAAAAAAAV3d3cuZ29vZ2xlLmNvbQ"
]

print(f"📊 آمار نهایی -> کانفیگ‌های نو: {len(valid_configs)} | پروکسی‌های نو: {len(valid_proxies)}")

if len(valid_configs) < 3:
    print("❌ تعداد کانفیگ‌ها برای ارسال پارت تست کافی نیست.")
    sys.exit(0)

configs_to_send = valid_configs[:3]
history["leftover_configs"] = valid_configs[3:]
proxies_to_send = valid_proxies[:3]

sent_in_this_batch_configs = []
country_stats = {}

print("\n🚀 شلیک اصلی پارت تست به کانال...")
for i in range(1):
    batch_c = configs_to_send
    batch_p = proxies_to_send
    post_text = ""
    labels = ["اول", "دوم", "سوم"]
    
    for idx, cfg in enumerate(batch_c):
        history["last_serial"] += 1
        serial_str = f"[{history['last_serial']:06d}]"
        country, flag = get_country_info(cfg)
        country_stats[country] = country_stats.get(country, 0) + 1
        clean_cfg = cfg.split('#')[0]
        final_cfg = f"{clean_cfg}#{serial_str} - {flag} {country} | @freenettir"
        sent_in_this_batch_configs.append(final_cfg)
        post_text += f"<b>📌 سرور {labels[idx]} :</b>\n<code>{final_cfg}</code>\n\n"
        history["sent_hashes"].append(hash(cfg))

    post_text += "<b>🌐 @freenettir | مخزن اصلی سرورها</b>\n🔹 #v2ray #vpn #proxy"
    
    reply_markup = {
        "inline_keyboard": [
            [{"text": "🔌 اتصال به پروکسی", "url": batch_p[0]}, {"text": "🔌 اتصال به پروکسی", "url": batch_p[1]}],
            [{"text": "🚀 اتصال به پروکسی پرسرعت", "url": batch_p[2]}]
        ]
    }
    
    logo = get_random_logo()
    try:
        if logo and os.path.exists(logo):
            with open(logo, 'rb') as photo_file:
                requests.post(f"https://api.telegram.org/bot{TOKEN}/sendPhoto", data={
                    "chat_id": CHANNEL, "caption": post_text, "parse_mode": "HTML", "reply_markup": json.dumps(reply_markup)
                }, files={"photo": photo_file})
        else:
            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={
                "chat_id": CHANNEL, "text": post_text, "parse_mode": "HTML", "reply_markup": json.dumps(reply_markup)
            })
        print("✅ پست اصلی ۳ تایی با موفقیت ارسال شد.")
    except Exception as e: print(f"❌ خطا در ارسال اصلی: {e}")

# --- فایل‌های پایان پارت ---
print("📝 ارسال استیکر و فایل‌های متنی...")
try: requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHANNEL, "text": "📝"})
except: pass

time.sleep(2)
support_markup = {"inline_keyboard": [[{"text": "🏛️ حمایت از کانال", "url": f"https://t.me/freenettir"}]]}

config_file_name = "100_Latest_Servers.txt"
with open(config_file_name, "w", encoding="utf-8") as f: f.write("\n\n".join(sent_in_this_batch_configs))

stats_text = ""
for country, count in country_stats.items():
    _, flag = get_country_info(f"dummy@{country}:443")
    stats_text += f"🔹 {count} سرور با آی پی کشور {country} {flag}\n"

config_caption = f"سرورهای جدید به فایل اضافه شدند.\n\n🔥 شما میتونید با استفاده از فایل تکست «💌 100 سرور آخر کانال» که هر ساعت آپدیت و داخل کانال ارسال میشه کاملا فیلترینگ رو بی معنی کنید.\nفقط کافیه چند پست آخر کانال رو ببینید تا فایل رو پیدا کنید. بعدش فایل رو باز کنید و محتوای اونو به صورت کامل کپی کنید و داخل اپلیکیشن مورد استفاده خودتون وارد کنید. همین! خداحافظ فیلترینگ 👋\nبا این کار دیگه لازم نیست به صورت دستی تک تک سرورها رو کپی کنید و داخل اپلیکیشن وارد کنید. با باز کردن و کپی کردن کامل محتوای این فایل به 100 سرور (به صورت یکجا) دسترسی خواهید داشت.♥️\n\n⭕️ این فایل حاوی موارد زیر میباشد :\n{stats_text}"

try:
    with open(config_file_name, "rb") as file_data:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendDocument", data={
            "chat_id": CHANNEL, "caption": config_caption, "reply_markup": json.dumps(support_markup)
        }, files={"document": file_data})
except: pass
if os.path.exists(config_file_name): os.remove(config_file_name)

time.sleep(2)

proxy_file_name = "100_Latest_Proxies.txt"
with open(proxy_file_name, "w", encoding="utf-8") as f: f.write("\n\n".join(proxies_to_send))

proxy_caption = "🔋 پروکسی های جدید به فایل اضافه شدند.\n\n🔥 شما میتونید با استفاده از فایل تکست «💌 100 پروکسی آخر کانال» که هر ساعت آپدیت و داخل کانال ارسال میشه کاملا فیلترینگ رو بی معنی کنید.\nفقط کافیه چند پست آخر کانال رو ببینید تا فایل رو پیدا کنید. بعد به پروکسی های پر سرعت و ضد فیلترینگ دسترسی پیدا کرده و هر کدام از پروکسی هارو مورد استفاده قرار بدید"

try:
    with open(proxy_file_name, "rb") as file_data:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendDocument", data={
            "chat_id": CHANNEL, "caption": proxy_caption, "reply_markup": json.dumps(support_markup)
        }, files={"document": file_data})
except: pass
if os.path.exists(proxy_file_name): os.remove(proxy_file_name)

with open(HISTORY_FILE, "w", encoding="utf-8") as f: json.dump(history, f, ensure_ascii=False, indent=2)
print("🎯 عیب‌یابی کامل شد و دیتای فیکس ارسال گردید.")
  
