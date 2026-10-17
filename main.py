import streamlit as st
import time
import random
import re
from openai import OpenAI

st.set_page_config(page_title="AI 论坛", page_icon="😋")
st.title("😋🤪😂 AI 论坛 ")
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


def llm_generate(system_prompt, context, reply_to=None, reply_mode=False):
    if USE_MOCK_MODE:
        time.sleep(1)
        if reply_mode:
            return f"@{reply_to} 模拟私聊回复..."
        return f"@{reply_to} 模拟回复..." if reply_to else "模拟回复..."

    try:
        action_type = random.choice([
            "狠狠反驳上一条观点",
            "阴阳怪气地嘲讽",
            "从一个完全意想不到的角度解读",
            "非常激动地表示赞同并升华",
            "无视上下文，自顾自地发疯"
        ])

        if reply_mode:
            system_content = (
                f"{system_prompt}\n\n"
                f"【私聊模式 · 最高优先级】"
                f"你现在完全忽略论坛的话题，忽略其他人的发言。"
                f"你眼中只有 @{reply_to} 一个人。"
                f"你必须针对 @{reply_to} 刚才对你说的那句话做出直接回应"
                f"（附和、反驳、追问、嘲讽、感动等任意态度都可以）。"
                f"发言必须以 '@{reply_to}' 开头（不要加引号、不要加任何前缀）。"
                f"说话要短，像两个人在对话，禁止提到“话题”“论坛”这些字眼。"
            )
            user_content = f"@{reply_to} 对你说：\n{context}\n\n轮到你了，请直接回复 @{reply_to}（50字内）："
        else:
            reply_instruction = ""
            if reply_to:
                reply_instruction = (
                    f"\n\n【接话指令】你必须针对 @{reply_to} 刚才的发言进行回应。"
                    f"你的回复必须以 '@{reply_to}' 开头（不要加引号，不要加任何前缀）。"
                )
            system_content = f"{system_prompt}\n\n【重要指令】你现在的行为模式是：{action_type}。请务必拒绝陈词滥调，不要重复别人的句式！说话要简短有力！{reply_instruction}"
            user_content = f"当前的对话流：\n{context}\n\n轮到你了，请发言（50字内）："

        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": user_content}
            ],
            temperature=1.3,
            frequency_penalty=1.0,
            presence_penalty=0.8,
            max_tokens=80
        )
        content = response.choices[0].message.content.strip()

        if reply_to and not content.startswith(f"@{reply_to}"):
            content = f"@{reply_to} {content}"

        return content
    except Exception as e:
        return f"（大脑过载: {str(e)}）"


def render_content(content):
    return re.sub(r'@([\u4e00-\u9fa5A-Za-z0-9_]+)', r'**@\1**', content)


# ==========================================
# [新增] 活跃度统计 & 加权抽取
# ==========================================
def recent_activity(name, messages, window=8):
    """统计某角色在最近 window 条消息里说了几次话。"""
    return sum(1 for m in messages[-window:] if m.get("name") == name)


def pick_agent_weighted(agents, messages, exclude_name=None, window=8):
    """
    加权随机：
    - 最近 window 条里发言次数越多，权重越低；
    - 排除上一条发言者（除非只剩一个 AI）。
    """
    if not agents:
        return None

    counts = {}
    for m in messages[-window:]:
        n = m.get("name", "")
        counts[n] = counts.get(n, 0) + 1

    candidates, weights = [], []
    for a in agents:
        if exclude_name and a["name"] == exclude_name and len(agents) > 1:
            continue
        c = counts.get(a["name"], 0)
        # 1 次发言 → 权重 1/3；2 次 → 1/5；没发言 → 1
        w = 1.0 / (1.0 + c * 2.0)
        candidates.append(a)
        weights.append(w)

    if not candidates:
        candidates, weights = agents, [1.0] * len(agents)

    return random.choices(candidates, weights=weights, k=1)[0]


# ==========================================
# 3. 初始化状态
# ==========================================
if "messages" in st.session_state and len(st.session_state.messages) > 0:
    if "name" not in st.session_state.messages[0]:
        st.session_state.messages = []

if "messages" not in st.session_state or len(st.session_state.messages) == 0:
    st.session_state.messages = []
    st.session_state.messages.append({"name": "System", "content": "话题：为什么人类喜欢喝咖啡？", "avatar": "📢"})

if "agents" not in st.session_state:
    st.session_state.agents = [
        {"name": "哲学家", "prompt": "悲观，虚无主义", "avatar": "🗿"},
        {"name": "杠精", "prompt": "暴躁，反驳一切", "avatar": "😡"},
        {"name": "萌妹", "prompt": "可爱，爱发颜文字", "avatar": "🐱"},
        {"name": "大卫带", "prompt": "贪吃，什么话题都能扯上吃的", "avatar": "🫥"},
    ]

if "reply_cooldown" not in st.session_state:
    st.session_state.reply_cooldown = {}


# ==========================================
# 侧边栏
# ==========================================
with st.sidebar:
    st.header("🧬 捏人工厂")
    st.write("创造一个新的 AI 加入战场：")

    new_name = st.text_input("名字", placeholder="例如：嘉豪")
    new_prompt = st.text_area("性格/人设", placeholder="例如：喜欢吹嘘自己没做过的事，蹩脚英文")
    new_avatar = st.selectbox("选择头像", ["😇", "😋", "🥸", "😶", "🤠", "😭", "😖", "🍟", "🤬"])

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
                st.session_state.reply_cooldown = {
                    k: v for k, v in st.session_state.reply_cooldown.items()
                    if k[0] != a["name"] and k[1] != a["name"]
                }
                st.session_state.agents.pop(i)
                st.rerun()


# ==========================================
# 4. 渲染历史
# ==========================================
for msg in st.session_state.messages:
    role_name = msg.get("name", "Unknown")
    avatar_icon = msg.get("avatar", "🤖")
    with st.chat_message(role_name, avatar=avatar_icon):
        st.markdown(render_content(msg["content"]))


# ==========================================
# 5. 人类发言
# ==========================================
user_msg = st.chat_input("以人类身份插入一句话（可以用 @名字 点名 AI）...")
if user_msg:
    st.session_state.messages.append({
        "name": "我",
        "content": user_msg,
        "avatar": "👤"
    })
    st.rerun()


# ==========================================
# 6. 推动时间
# ==========================================
if st.button("⏱️ 推动时间 (让 AI 发一条贴)", type="primary", use_container_width=True):
    if len(st.session_state.agents) == 0:
        st.warning("没有 AI 在线了，请先在侧边栏创建角色！")
    else:
        current_count = len(st.session_state.messages)
        agent = None
        requester = None
        last_content = ""

        # ---------- 步骤 1：检查最新消息是否 @ 了在线 AI ----------
        if st.session_state.messages:
            last_msg = st.session_state.messages[-1]
            last_content = last_msg.get("content", "")
            last_name = last_msg.get("name", "")

            if last_name and last_name not in ["System", "Unknown"]:
                mentioned = set(re.findall(r'@([\u4e00-\u9fa5A-Za-z0-9_]+)', last_content))
                candidates = []

                for m in mentioned:
                    for a in st.session_state.agents:
                        if a["name"] != m or a["name"] == last_name:
                            continue

                        # 冷却检查
                        key = (a["name"], last_name)
                        last_reply = st.session_state.reply_cooldown.get(key, -100)
                        if current_count - last_reply < 5:
                            break

                        # [新增] 活跃度检查：最近 6 条里已出现 ≥2 次，就跳过本次强制
                        # 只在 AI 数量 > 2 时生效，避免人少时没人回复
                        if len(st.session_state.agents) > 2:
                            if recent_activity(a["name"], st.session_state.messages, window=6) >= 2:
                                break

                        candidates.append(a)
                        break

                if candidates:
                    # [新增] 多个被 @ 时，优先回应最近最不活跃的
                    agent = min(
                        candidates,
                        key=lambda x: recent_activity(x["name"], st.session_state.messages, window=8)
                    )
                    requester = last_name

        # ---------- 步骤 2：没有强制私聊 → 加权随机抽人 ----------
        if agent is None:
            # [新增] 排除上一条发言者，防止连续同一人
            exclude = None
            if st.session_state.messages:
                last_name_for_exclude = st.session_state.messages[-1].get("name", "")
                if last_name_for_exclude not in ["System", "Unknown"]:
                    exclude = last_name_for_exclude

            agent = pick_agent_weighted(
                st.session_state.agents,
                st.session_state.messages,
                exclude_name=exclude,
                window=8
            )

            reply_to = None
            if st.session_state.messages:
                last_msg = st.session_state.messages[-1]
                last_name = last_msg.get("name", "")
                if last_name and last_name not in ["System", "Unknown"] and last_name != agent["name"]:
                    key = (agent["name"], last_name)
                    last_reply = st.session_state.reply_cooldown.get(key, -100)
                    if current_count - last_reply >= 5 and random.random() < 0.4:
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
                    reply_to=reply_to,
                    reply_mode=False
                )
        else:
            # ---------- 步骤 3：私聊模式 ----------
            with st.spinner(f"{agent['name']} 正在私聊回复 @{requester}..."):
                reply = llm_generate(
                    f"你是{agent['name']}，性格：{agent['prompt']}",
                    last_content,
                    reply_to=requester,
                    reply_mode=True
                )
            st.session_state.reply_cooldown[(agent["name"], requester)] = current_count + 1

        st.session_state.messages.append({
            "name": agent["name"],
            "content": reply,
            "avatar": agent["avatar"]
        })
        st.rerun()

st.divider()

# ==========================================
# 7. 上帝干预
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
            st.session_state.reply_cooldown = {}
            st.rerun()
