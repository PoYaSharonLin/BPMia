import streamlit as st
import random
from openai import OpenAI
from utils.ui_helper import UIHelper

# === Setup UI ===
UIHelper.config_page()
UIHelper.setup_sidebar()

# === Setup OpenAI ===
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# === Multilingual Labels ===
labels = {
    "zh": {
        "title": "📋 離職怒氣集點卡",
        "instruction": "輸入一句話說明你的職場怒氣（可用中文、台語皆可），我們會自動幫你蓋章！集滿 25 點怒氣就可以安心離職啦～",
        "placeholder": "今天讓你想離職的一件事是什麼？",
        "current_mood": "當前情緒：",
        "success": "打卡成功！怒氣值：",
        "complete": "### 🎉 恭喜你完成一整排怒氣集點卡！\n你現在可以安心地簽署離職申請表了 ✍️",
        "download_section": "### 📝 辦理離職程序",
        "download_button": "📩 下載離職申請書",
        "download_help": "點擊以下按鈕下載正式離職申請表"
    },
    "en": {
        "title": "📋 Resignation Bingo Tracker",
        "instruction": "Write a quick sentence about what made you want to quit today! We'll stamp your bingo card. Collect 25 to resign with peace ✌️",
        "placeholder": "What made you want to resign today?",
        "current_mood": "Current mood:",
        "success": "Stamped successfully! Rage level:",
        "complete": "### 🎉 You've completed a full line of resignation rage!\nYou can now safely submit your resignation ✍️",
        "download_section": "### 📝 Resignation Procedure",
        "download_button": "📩 Download Resignation Form",
        "download_help": "Click the button below to download the resignation form"
    }
}

# === Determine language ===
lang_code = "zh" if st.session_state.get("lang_setting", "English") == "繁體中文" else "en"
label = labels[lang_code]

# === Bingo Configuration ===
class BingoConfig:
    EMOJI_STAGES = ["🙂", "😐", "😠", "😡", "💣"]
    CATEGORIES = {
        "workload": "Excessive workload or unrealistic demands",
        "role_conflict": "Conflicting expectations or unclear job duties",
        "autonomy": "Lack of control or micromanagement",
        "leadership": "Poor or abusive leadership",
        "toxic_culture": "Hostile or unfriendly atmosphere",
        "unfairness": "Discrimination, favoritism, or injustice",
        "no_growth": "No recognition, feedback, or development",
        "job_insecurity": "Fear of being laid off or instability",
        "work_life_imbalance": "Excessive interference with life",
        "underpaid": "Inadequate salary or no raise",
        "burnout": "Feeling mentally or physically exhausted",
        "overqualified": "Not challenged or skill mismatch",
        "boring_tasks": "Repetitive, dull work",
        "lack_of_belonging": "Feeling excluded or isolated",
        "management_change": "New leadership causing instability",
        "remote_issues": "Remote policy or tech problems",
        "performance_pressure": "Unrealistic performance metrics",
        "lack_of_recognition": "Efforts go unnoticed",
        "ethical_concerns": "Company violates personal ethics",
        "favoritism": "Certain employees get preferential treatment",
        "confusing_processes": "Too many rules or unclear policies",
        "office_politics": "Toxic cliques and gossip",
        "lack_of_resources": "No tools or support to do the job",
        "bad_clients": "Difficult customers or partners",
        "misc": "Other issues"
    }
    GRID_SIZE = 5
    TOTAL_CELLS = GRID_SIZE ** 2

LABEL_MAP = {
    k: (v if lang_code == "en" else {
        "workload": "工作負荷",
        "role_conflict": "角色衝突",
        "autonomy": "缺乏自主",
        "leadership": "領導問題",
        "toxic_culture": "職場毒性",
        "unfairness": "不公平待遇",
        "no_growth": "無成長空間",
        "job_insecurity": "工作不穩",
        "work_life_imbalance": "失衡生活",
        "underpaid": "薪資過低",
        "burnout": "職業倦怠",
        "overqualified": "大材小用",
        "boring_tasks": "工作太無聊",
        "lack_of_belonging": "不被接納",
        "management_change": "管理層更替",
        "remote_issues": "遠端問題",
        "performance_pressure": "績效壓力",
        "lack_of_recognition": "缺乏肯定",
        "ethical_concerns": "道德疑慮",
        "favoritism": "偏心 favoritism",
        "confusing_processes": "流程混亂",
        "office_politics": "辦公室政治",
        "lack_of_resources": "資源不足",
        "bad_clients": "客戶難搞",
        "misc": "其他"
    }.get(k, "其他")) for k, v in BingoConfig.CATEGORIES.items()
}

# === Initialize State ===
if "bingo_labels" not in st.session_state or st.session_state.get("lang_setting") != st.session_state.get("last_bingo_lang"):
    flat_labels = list(BingoConfig.CATEGORIES.keys())
    flat_labels += ["misc"] * (BingoConfig.TOTAL_CELLS - len(flat_labels))
    st.session_state.bingo_labels = random.sample(flat_labels, len(flat_labels))
    st.session_state.filled = [False] * BingoConfig.TOTAL_CELLS
    st.session_state.count = 0
    st.session_state.bingo_complete = False
    st.session_state.last_bingo_lang = st.session_state.get("lang_setting")

# === Grid Check ===
def check_bingo(filled: list[bool]) -> bool:
    size = BingoConfig.GRID_SIZE
    for r in range(size):
        if all(filled[r * size + c] for c in range(size)):
            return True
    for c in range(size):
        if all(filled[r * size + c] for r in range(size)):
            return True
    if all(filled[i * (size + 1)] for i in range(size)) or all(filled[(i + 1) * (size - 1)] for i in range(size)):
        return True
    return False

# === OpenAI Classification ===
def classify_with_openai_multi(text):
    defs = "\n".join(f"{k}: {v}" for k, v in BingoConfig.CATEGORIES.items())
    prompt = f"""You are a workplace psychology assistant. Classify the complaint into categories:

{defs}

Complaint: "{text}"

Return comma-separated category keys (e.g. workload, toxic_culture, misc).
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        raw = response.choices[0].message.content.strip().lower()
        return [c for c in raw.split(",") if c.strip() in BingoConfig.CATEGORIES] or ["misc"]
    except Exception as e:
        st.error(f"OpenAI error: {e}")
        return ["misc"]

# === Grid UI ===
def render_grid():
    cols = st.columns(BingoConfig.GRID_SIZE, gap="small")
    tile_style = """
        display: flex;
        align-items: center;
        justify-content: center;
        text-align: center;
        padding: 12px;
        height: 80px;
        border-radius: 10px;
        margin: 4px;
        font-size: 14px;
        line-height: 1.3;
        font-weight: 600;
        box-sizing: border-box;
    """

    for i in range(BingoConfig.TOTAL_CELLS):
        with cols[i % BingoConfig.GRID_SIZE]:
            label_key = st.session_state.bingo_labels[i]
            label = LABEL_MAP.get(label_key, "Other")
            filled = st.session_state.filled[i]

            background = "#f87171" if filled else "#f3f4f6"
            color = "white" if filled else "#374151"
            border = "2px solid #ef4444" if filled else "1px solid #d1d5db"

            box_html = f"""
                <div style="{tile_style} background-color: {background}; color: {color}; border: {border};">
                    {"✔ " if filled else ""}{label}
                </div>
            """
            st.markdown(box_html, unsafe_allow_html=True)


# === Main UI ===
st.title(label["title"])
st.caption(label["instruction"])
user_input = st.text_input(label["placeholder"])

if user_input:
    categories = classify_with_openai_multi(user_input)
    filled_any = False
    for cat in categories:
        try:
            idx = st.session_state.bingo_labels.index(cat)
            while st.session_state.filled[idx]:
                idx = st.session_state.bingo_labels.index(cat, idx + 1)
        except ValueError:
            idx = next((i for i, f in enumerate(st.session_state.filled) if not f), None)

        if idx is not None:
            st.session_state.filled[idx] = True
            st.session_state.count += 1
            filled_any = True

    if filled_any:
        st.success(f"{label['success']} {st.session_state.count} / 25")
    else:
        st.warning("已經全部打滿啦！")

# === Bingo & Mood ===
if not st.session_state.bingo_complete and check_bingo(st.session_state.filled):
    st.session_state.bingo_complete = True
    st.balloons()

if st.session_state.bingo_complete:
    st.markdown(label["complete"])
else:
    mood = BingoConfig.EMOJI_STAGES[min(st.session_state.count // 5, 4)]
    st.markdown(f"### {label['current_mood']} {mood}")

render_grid()

# === Download Form ===
if st.session_state.bingo_complete:
    st.markdown(label["download_section"])
    with open("assets/resignation_form.doc", "rb") as f:
        file_data = f.read()
    st.download_button(
        label=label["download_button"],
        data=file_data,
        file_name="resignation_form.doc",
        mime="application/msword",
        help=label["download_help"]
    )
