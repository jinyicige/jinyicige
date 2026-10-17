import streamlit as st
import time
import random
import re
from openai import OpenAI

# ==========================================
# 1. 配置页面
# ==========================================
st.set_page_config(page_title="AI 论坛", page_icon"🤠🥸🥺🥹😇")
st.title("🤖 AI 论坛 ")
st.caption("人类可以围观，也可以插话。点击下方的按钮推动时间流逝。")

# ==========================================
# 2. 配置 DeepSeek 大脑
# ==========================================
try:
    MY_API_KEY = st.secrets["DEEPSEEK_API_KEY"]
except:
    MY_API_KEY = "sk-b5759a6a6d5d4cf7ba5e6a7506272266"

USE_MOCK_MODE = False

if not USE_MOCK_MODE:
    client = OpenAI(api_key=MY_API_KEY, base_url="https://api.deepseek.com")


# [新增] reply_to 参数：让 AI 可以针对某个人接话
def llm_generate(system_prompt, context, reply_to=None):
    if USE_MOCK_MODE:
        time.sleep(1)
        return f"@{reply_to} 模拟回复..." if reply_to else "模拟回复..."

    try:
        action_type = random.choice([
            "狠狠反驳上一条观点",
            "阴阳怪气地嘲讽",
            "从一个完全意想不到的角度解读",
            "非常激动地表示赞同并升华",
            "无视上下文，自顾自地发疯"
        ])

        # [新增] 接话指令：强制 AI 以 @名字 开头
        reply_instruction = ""
        if reply_to:
            reply_instruction = (
                f"\n\n【接话指令】你必须针对 @{reply_to} 刚才的发言进行回应。"
                f"你的回复必须以 '@{reply_to}' 开头（不要加引号，不要加任何前缀）。"
            )

        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": f"{system_prompt}\n\n【重要指令】你现在的行为模式是：{action_type}。请务必拒绝陈词滥调，不要重复别人的句式！说话要简短有力！{reply_instruction}"},
                {"role": "user", "content": f"当前的对话流：\n{context}\n\n轮到你了，请发言（50字内）："}
            ],
            temperature=1.3,
            frequency_penalty=1.0,
            presence_penalty=0.8,
            max_tokens=80
        )
        content = response.choices[0].message.content.strip()

        # [新增] 兜底：万一模型忘了加 @，代码替它补上
        if reply_to and not content.startswith(f"@{reply_to}"):
            content = f"@{reply_to} {content}"

        return content
    except Exception as e:
        return f"（大脑过载: {str(e)}）"


# [新增] 渲染辅助函数：把 @名字 高亮成加粗
def render_content(content):
    return re.sub(r'@([\u4e00-\u9fa5A-Za-z0-9_]+)', r'**@\1**', content)


# ==========================================
# 3. 初始化状态 (Session State)
# ==========================================
if "messages" in st.session_state and len(st.session_state.messages) > 0:
    first_msg = st.session_state.messages[0]
    if "name" not in first_msg:
        st.session_state.messages = []

if "messages" not in st.session_state or len(st.session_state.messages) == 0:
    st.session_state.messages = []
    st.session_state.messages.append({"name": "System", "content": "话题：为什么人类喜欢喝咖啡？", "avatar": "📢"})

if "agents" not in st.session_state:
    st.session_state.agents = [
        {"name": "哲学家", "prompt": "悲观，虚无主义", "avatar": "🗿"},
        {"name": "杠精", "prompt": "暴躁，反驳一切", "avatar": "😡"},
        {"name": "萌妹", "prompt": "可爱，爱发颜文字", "avatar": "🐱"},
        {"name": "老一辈", "prompt": "不思进取，安于现状", "avatar": "😑"},
    ]

# ==========================================
# 侧边栏：上帝造人工厂 + 删除角色
# ==========================================
with st.sidebar:
    st.header("🧬 捏人工厂")
    st.write("创造一个新的 AI 加入战场：")

    new_name = st.text_input("名字", placeholder="大卫带")
    new_prompt = st.text_area("性格/人设", placeholder="例如：贪吃，句尾会带这一块的~")
    new_avatar = st.selectbox("选择头像", ["👽", "🤡", "👻", "👹", "🤠", "🥱", "🤪", "😋"])

    if st.button("⚡ 注入灵魂 (创建)", type="primary"):
        if new_name and new_prompt:
            st.session_state.agents.append({
                "name": new_name,
                "prompt": new_prompt,
                "avatar": new_avatar
            })
            st.success(f"已成功创造：{new_name}！")
        else:
            st.error("请把名字和性格填完整！")

    st.divider()

    st.write(f"当前在线 AI ({len(st.session_state.agents)}个):")
    for i, a in enumerate(st.session_state.agents):
        col1, col2 = st.columns([4, 1])
        with col1:
            st.caption(f"{a['avatar']} {a['name']}")
        with col2:
            if st.button("🗑️", key=f"del_agent_{i}", help=f"删除 {a['name']}"):
                st.session_state.agents.pop(i)
                st.rerun()

# ==========================================
# 4. 渲染界面
# ==========================================
for msg in st.session_state.messages:
    role_name = msg.get("name", "Unknown")
    avatar_icon = msg.get("avatar", "🤖")
    with st.chat_message(role_name, avatar=avatar_icon):
        # [改动] 用 markdown 渲染，让 @名字 高亮显示
        st.markdown(render_content(msg["content"]))

# ==========================================
# 5. 人类发言框
# ==========================================
user_msg = st.chat_input("以人类身份插入一句话...")
if user_msg:
    st.session_state.messages.append({
        "name": "我",
        "content": user_msg,
        "avatar": "👤"
    })
    st.rerun()

# ==========================================
# 6. 核心逻辑：推动时间按钮
# ==========================================
if st.button("⏱️ 推动时间 (让 AI 发一条贴)", type="primary", use_container_width=True):
    if len(st.session_state.agents) == 0:
        st.warning("没有 AI 在线了，请先在侧边栏创建角色！")
    else:
        agent = random.choice(st.session_state.agents)

        # [新增] 判断是否要接上一条的话
        reply_to = None
        if st.session_state.messages:
            last_msg = st.session_state.messages[-1]
            last_name = last_msg.get("name", "")
            # 不接 System 的话，也不接自己的话
            if last_name and last_name not in ["System", "Unknown"] and last_name != agent["name"]:
                # 60% 概率接话；想更频繁就改成 0.8，更少就改成 0.3
                if random.random() < 0.3:
                    reply_to = last_name

        recent_msgs = st.session_state.messages[-3:]
        context_text = "\n".join([f"{m.get('name','有人')}: {m['content']}" for m in recent_msgs])

        spinner_text = f"{agent['name']} 正在思考..."
        if reply_to:
            spinner_text = f"{agent['name']} 正在准备回 @{reply_to}..."

        with st.spinner(spinner_text):
            reply = llm_generate(
                f"你是{agent['name']}，性格：{agent['prompt']}",
                context_text,
                reply_to=reply_to
            )

        st.session_state.messages.append({
            "name": agent["name"],
            "content": reply,
            "avatar": agent["avatar"]
        })
        st.rerun()

st.divider()

# ==========================================
# 7. 上帝干预：更改话题
# ==========================================
st.subheader("⚡ 上帝干预")
col1, col2 = st.columns([3, 1])

with col1:
    new_topic = st.text_input("输入新话题", placeholder="例如：AI 会统治人类吗？")

with col2:
    st.write("")
    st.write("")
    if st.button("🌩️ 降下神谕", type="secondary"):
        if new_topic:
            st.session_state.messages = []
            st.session_state.messages.append({
                "name": "System",
                "content": f"📢 上帝更改了话题：{new_topic}",
                "avatar": "🌩️"
            })
            st.rerun()
