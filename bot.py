import os
import sys
import time
import json
import re
import random
import requests

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHANNEL = os.environ.get("TELEGRAM_CHANNEL")

if not TOKEN or not CHANNEL:
    print("خطا: سکرت‌های تلگرام در گیت‌هاب تنظیم نشده‌اند!")
    sys.exit(1)

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

config_sources = [
    "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/sub_merge.txt",
    "https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/v2ray/mix",
    "https://raw.githubusercontent.com/Borders-Freedom/Sub-Collector/main/sub/mix"
]

proxy_sources = [
    "https://raw.githubusercontent.com/Grim1313/mtproto-for-telegram/master/all_proxies.txt",
    "https://raw.githubusercontent.com/SoliSpirit/mtproto/master/all_proxies.txt"
]

raw_configs = []
raw_proxies = []

print("در حال جمع‌آوری اطلاعات از مخازن...")
for url in config_sources:
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            found = re.findall(r'((?:vless|trojan|ss)://[^\s#"\'>]+)', res.text)
            raw_configs.extend(found)
    except: pass

for url in proxy_sources:
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            found = re.findall(r'((?:https://t\.me|tg)://proxy\?server=[^\s"\'><]+)', res.text)
            for p in found: raw_proxies.append(p.replace("tg://", "https://t.me/"))
    except: pass

valid_configs = history["leftover_configs"]
for c in raw_configs:
    if hash(c) not in history["sent_hashes"] and c not in valid_configs: valid_configs.append(c)

valid_proxies = history["leftover_proxies"]
for p in raw_proxies:
    if p not in valid_proxies and p not in history["sent_proxies_hashes"]: valid_proxies.append(p)

print(f"تعداد کل کانفیگ‌های موجود: {len(valid_configs)} | پروکسی‌ها: {len(valid_proxies)}")

if len(valid_configs) < 99 or len(valid_proxies) < 99:
    print("دیتا به حد نصاب ۹۹ عدد نرسیده است. ذخیره برای پارت بعد.")
    history["leftover_configs"] = valid_configs
    history["leftover_proxies"] = valid_proxies
    with open(HISTORY_FILE, "w", encoding="utf-8") as f: json.dump(history, f, ensure_ascii=False, indent=2)
    sys.exit(0)

configs_to_send = valid_configs[:99]
history["leftover_configs"] = valid_configs[99:]
proxies_to_send = valid_proxies[:99]
history["leftover_proxies"] = valid_proxies[99:]

sent_in_this_batch_configs = []
country_stats = {}

print("🚀 شروع ارسال منظم پست‌های ۳ تایی...")
for i in range(33):
    batch_c = configs_to_send[i*3 : (i+1)*3]
    batch_p = proxies_to_send[i*3 : (i+1)*3]
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
        post_text += f"📌 سرور {labels[idx]} :\n`{final_cfg}`\n\n"
        history["sent_hashes"].append(hash(cfg))

    post_text += "🌐 @freenettir | مخزن اصلی سرورها\n🔹 #v2ray #vpn #proxy"
    
    reply_markup = {
        "inline_keyboard": [
            [{"text": "🔌 اتصال به پروکسی", "url": batch_p[0]}, {"text": "🔌 اتصال به پروکسی", "url": batch_p[1]}],
            [{"text": "🚀 اتصال به پروکسی پرسرعت", "url": batch_p[2]}]
        ]
    }
    for bp in batch_p: history["sent_proxies_hashes"].append(bp)
        
    logo = get_random_logo()
    try:
        if logo and os.path.exists(logo):
            with open(logo, 'rb') as photo_file:
                requests.post(f"https://api.telegram.org/bot{TOKEN}/sendPhoto", data={
                    "chat_id": CHANNEL, "caption": post_text, "parse_mode": "Markdown", "reply_markup": json.dumps(reply_markup)
                }, files={"photo": photo_file})
        else:
            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={
                "chat_id": CHANNEL, "text": post_text, "parse_mode": "Markdown", "reply_markup": json.dumps(reply_markup)
            })
    except Exception as e: print(f"خطا در ارسال: {e}")

    if i < 32: time.sleep(54)

print("📝 ارسال استیکر و فایل‌ها...")
try: requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHANNEL, "text": "📝"})
except: pass

time.sleep(3)
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

time.sleep(5)

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

if len(history["sent_hashes"]) > 10000: history["sent_hashes"] = history["sent_hashes"][-5000:]
if len(history["sent_proxies_hashes"]) > 5000: history["sent_proxies_hashes"] = history["sent_proxies_hashes"][-2000:]

with open(HISTORY_FILE, "w", encoding="utf-8") as f: json.dump(history, f, ensure_ascii=False, indent=2)
print("🎯 پارت تست با موفقیت به پایان رسید.")
