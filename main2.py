import os
import json
import csv
import requests
import time

# --- الإعدادات ---
# مفتاح API الخاص بك
API_KEY = "sk_f0db6a5c611ffda8d488dd7f02dcf4f8533458a821fc830c"

# النص المراد تحويله إلى كلام باللغة العربية
TTS_TEXT = """<speak>
  أهلاً بكم في موقعنا، كاستينج فويس أوف، أول منصة للتعليق الصوتي في المغرب وأول ذكاء اصطناعي مغربي مئة بالمئة.
</speak>
"""

# الموديل المستخدم من ElevenLabs
MODEL_ID = "eleven_multilingual_v2"

# إعدادات الصوت لتحقيق توازن بين الوضوح والأداء
VOICE_SETTINGS = {
    "stability": 0.7,
    "similarity_boost": 0.75,
    "style": 0.3,
    "use_speaker_boost": True
}

# أسماء الملفات والمجلدات للمخرجات العربية
FAVORITES_FILE = "favorite-voices (1)ARAB.txt"
VOICES_JSON_FILE = "all_shared_voices_updated.json"
OUTPUT_AUDIO_DIR = "audios_ar"
OUTPUT_CSV_FILE = "voice_map_ar.csv"

# --- دوال مساعدة ---

def get_api_headers():
    """ترجع الترويسات القياسية لطلبات API."""
    return { "Accept": "application/json", "xi-api-key": API_KEY }

def get_current_library_voices():
    """تجلب قائمة الأصوات الموجودة حاليًا في مكتبتك الشخصية."""
    url = "https://api.elevenlabs.io/v1/voices"
    try:
        response = requests.get(url, headers=get_api_headers())
        if response.status_code == 200:
            return response.json().get('voices', [])
    except requests.exceptions.RequestException as e:
        print(f"  -> خطأ في الشبكة أثناء جلب أصوات المكتبة: {e}")
    return []

def delete_voice_from_library(private_voice_id):
    """تحذف صوتًا من مكتبتك الشخصية."""
    print(f"  -> جاري حذف الصوت '{private_voice_id}' لتوفير مساحة...")
    url = f"https://api.elevenlabs.io/v1/voices/{private_voice_id}"
    requests.delete(url, headers=get_api_headers())

def call_tts_api(voice_id, name):
    """تستدعي API الخاص بـ TTS وترجع كائن الاستجابة."""
    print(f"\nمحاولة إنشاء مقطع صوتي لـ '{name}' (المعرف: {voice_id})...")
    api_url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {**get_api_headers(), "Content-Type": "application/json"}
    data = {"text": TTS_TEXT, "model_id": MODEL_ID, "voice_settings": VOICE_SETTINGS}
    try:
        return requests.post(api_url, json=data, headers=headers)
    except requests.exceptions.RequestException as e:
        print(f"  -> خطأ في الشبكة أثناء استدعاء TTS: {e}")
        return None

def save_audio_file(response_content, name):
    """تحفظ المحتوى الصوتي في ملف."""
    filename = f"{name}.mp3"
    filepath = os.path.join(OUTPUT_AUDIO_DIR, filename)
    with open(filepath, 'wb') as f:
        f.write(response_content)
    print(f"  -> تم حفظ الملف '{filepath}' بنجاح")

# --- المنطق الرئيسي للبرنامج ---

def run_process():
    # تحميل وتجهيز بيانات الأصوات
    try:
        with open(FAVORITES_FILE, 'r', encoding='utf-8') as f:
            favorite_names = {line.strip() for line in f if line.strip() and "Selection" not in line}
        with open(VOICES_JSON_FILE, 'r', encoding='utf-8') as f:
            all_voices_data = json.load(f).get("voices", [])
        
        voice_map = {v['name']: v['voice_id'] for v in all_voices_data if v['name'] in favorite_names}
        ordered_favorites = sorted([name for name in favorite_names if name in voice_map])
    except Exception as e:
        print(f"خطأ: فشل في تحميل البيانات الأولية. {e}")
        return

    os.makedirs(OUTPUT_AUDIO_DIR, exist_ok=True)
    
    # التحقق من الملفات الموجودة مسبقًا لتجنب إعادة العمل
    try:
        existing_files = os.listdir(OUTPUT_AUDIO_DIR)
        existing_voice_names = {os.path.splitext(f)[0] for f in existing_files if f.endswith('.mp3')}
        print(f"تم العثور على {len(existing_voice_names)} ملف صوتي موجود مسبقًا في '{OUTPUT_AUDIO_DIR}'.")
    except FileNotFoundError:
        existing_voice_names = set()

    # --- هذا هو السطر الذي تم تصحيحه ---
    voices_to_process = [name for name in ordered_favorites if name not in existing_voice_names]
    
    if not voices_to_process:
        print("\nجميع الأصوات المطلوبة تم إنشاؤها بالفعل. لا يوجد شيء لفعله.")
        return
        
    print(f"سيتم تخطي {len(existing_voice_names)} صوت. سيتم معالجة {len(voices_to_process)} صوت جديد.")

    csv_data = []
    
    # حلقة المعالجة الرئيسية
    for i, name in enumerate(voices_to_process):
        public_id = voice_map[name]
        response = call_tts_api(public_id, name)
        
        if response and response.status_code == 200:
            save_audio_file(response.content, name)
            csv_data.append([name, f"{name}.mp3"])
            continue

        if not response: continue 

        error_detail = response.json().get("detail", {})
        status = error_detail.get("status")

        if status == "add_limit_reached":
            print("\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            print("!!! مكتبة الأصوات ممتلئة (30 صوتًا).")
            print("!!! فشل الصوت الأخير. للمتابعة، يجب على البرنامج التحول إلى")
            print("!!! وضع 'الحذف ثم الإضافة'، الذي يستهلك من حصتك الشهرية.")
            print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            
            try:
                remaining_count = len(voices_to_process) - i
                confirm = input(f"\n>>> هل تريد المتابعة مع الأصوات المتبقية وعددها {remaining_count}؟ (اكتب 'نعم' للتأكيد): ")
            except EOFError:
                confirm = "no"

            if confirm.strip() == 'نعم':
                print("\n--- التحويل إلى وضع التدوير ---")
                remaining_in_cycle = voices_to_process[i:]
                for cycle_name in remaining_in_cycle:
                    library_voices = get_current_library_voices()
                    if not library_voices:
                        print("  -> خطأ: المكتبة فارغة ولكن تم الوصول للحد الأقصى؟ لا يمكن الحذف. سيتم التوقف.")
                        break
                    
                    delete_voice_from_library(library_voices[0]['voice_id'])
                    
                    cycle_public_id = voice_map[cycle_name]
                    cycle_response = call_tts_api(cycle_public_id, cycle_name)
                    
                    if cycle_response and cycle_response.status_code == 200:
                        save_audio_file(cycle_response.content, cycle_name)
                        csv_data.append([cycle_name, f"{cycle_name}.mp3"])
                    else:
                        print(f"  -> خطأ فادح: فشلت معالجة '{cycle_name}' حتى بعد توفير مساحة. سيتم إيقاف وضع التدوير.")
                        if cycle_response and cycle_response.json().get("detail", {}).get("status") == "voice_add_edit_limit_reached":
                            print(f"  -> السبب: تم الوصول للحد الأقصى من حصة الإضافة/التعديل الشهرية.")
                        break 
                break 
            else:
                print("\nلم يقم المستخدم بالتأكيد. سيتم إيقاف البرنامج.")
                break 

        elif status == "voice_add_edit_limit_reached":
            print(f"\nخطأ فادح: تم الوصول للحد الشهري لعمليات إضافة/تعديل الأصوات. لا يمكن المتابعة. الرسالة: {error_detail.get('message')}")
            break 
        else:
            print(f"\nخطأ: حدث خطأ غير معروف للصوت '{name}'. الاستجابة: {response.text}")

    # --- إنشاء التقرير النهائي (مع الإضافة للملف الموجود) ---
    print("\n--- انتهت المعالجة ---")
    if csv_data:
        try:
            file_exists = os.path.isfile(OUTPUT_CSV_FILE)
            with open(OUTPUT_CSV_FILE, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(['id', 'filename'])
                writer.writerows(sorted(csv_data))
            print(f"تمت إضافة {len(csv_data)} إدخال جديد بنجاح إلى الملف '{OUTPUT_CSV_FILE}'.")
        except IOError as e:
            print(f"\nخطأ: لم أتمكن من الكتابة إلى ملف CSV: {e}")
    else:
        print("لم يتم إنشاء أي ملفات صوتية جديدة في هذه الجلسة.")

if __name__ == "__main__":
    run_process()