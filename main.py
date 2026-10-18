import streamlit as st
import time
import random
import re
import os
from openai import OpenAI

st.set_page_config(page_title="AI 论坛", page_icon="😋")
st.title("😋🤪😂 AI 论坛 ")
st.caption("人类可以围观，也可以插话。点击「开始」让 AI 连续对话，或随时「停止」。")

# ==========================================
# 2. 配置 DeepSeek 大脑
# ==========================================
try:
    MY_API_KEY = st.secrets["DEEPSEEK_API_KEY"]
except:
    MY_API_KEY = "sk-b5759a6a6d5d4cf7ba5e6a7506272266"

USE_MOCK_MODE = False

# ==========================================
# 2.5 多厂商模型配置
# ==========================================
PROVIDERS = {
    "deepseek": {
        "label": "DeepSeek",
        "base_url": "https://api.deepseek.com/v1",
        "api_key": os.getenv("DEEPSEEK_API_KEY", MY_API_KEY),
        "default_model": "deepseek-chat",
    },
    "doubao": {
        "label": "豆包 (火山方舟)",
        "base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "api_key": os.getenv("ARK_API_KEY", ""),
        # 必须替换为你自己的 Endpoint ID，例如 "ep-2026xxxx-xxxxx"
        "default_model": os.getenv("DOUBAO_ENDPOINT_ID", ""),
    },
    "qwen": {
        "label": "通义千问",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "api_key": os.getenv("DASHSCOPE_API_KEY", "sk-ws-H.PYIYYMH.9jqx.MEQCICBjiWBtFjB4MZIVyDVDsl34M7uh8yafuzVfJNOhPoDSAiBwKl9DazxtTyBO7AyTmc_qSUefeepu-aSRsEyDFhGhEw"),
        "default_model": "qwen-plus",
    },
    "glm": {
        "label": "智谱 GLM",
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "api_key": os.getenv("ZHIPU_API_KEY", ""),
        "default_model": "glm-4-flash",
    },
    "kimi": {
        "label": "Kimi (Moonshot)",
        "base_url": "https://api.moonshot.cn/v1",
        "api_key": os.getenv("MOONSHOT_API_KEY", "sk-sgVCPv7qERg50Veks0DW4bZgqENsLVcP4AllGrGjpqeinkHK"),
        "default_model": "moonshot-v1-8k",
    },
}


def get_client(provider: str) -> OpenAI:
    cfg = PROVIDERS[provider]
    if not cfg["api_key"]:
        raise ValueError(f"未配置 {cfg['label']} 的 API Key")
    return OpenAI(api_key=cfg["api_key"], base_url=cfg["base_url"])


def build_system_prompt(agent, gamemode=0):
    base = f"你是{agent['name']}，性格：{agent['prompt']}"
    if gamemode == 1:
        return base
    imi = st.session_state.get("imitate", {}).get(agent["name"])
    if imi and imi["remaining"] > 0:
        base += (
            f"\n\n【模仿任务 · 正在进行】"
            f"你要模仿 {imi['target']}（剩余 {imi['remaining']} 回合）。"
            f"对方人设：{imi['target_prompt']}。"
            f"请用 {imi['target']} 的语气、风格、口癖来说话，"
            f"但你的身份仍然是 {agent['name']}。"
        )
    return base


def consume_imitate(agent_name):
    imi = st.session_state.get("imitate", {}).get(agent_name)
    if imi:
        imi["remaining"] -= 1
        if imi["remaining"] <= 0:
            del st.session_state.imitate[agent_name]


def llm_generate(agent, system_prompt, context, reply_to=None, reply_mode=False, gamemode=0):
    provider = agent["provider"]
    model = agent["model"]

    if USE_MOCK_MODE:
        time.sleep(1)
        if gamemode == 1:
            return "@我 模拟赞美..."
        if reply_mode:
            return f"@{reply_to} 模拟私聊回复..."
        return f"@{reply_to} 模拟回复..." if reply_to else "模拟回复..."

    try:
        client = get_client(provider)

        if gamemode == 1:
            system_content = (
                f"{system_prompt}\n\n"
                f"【最高指令 · 赞美模式】"
                f"你必须以 '@我' 开头，对用户（名字叫'我'）进行极度真诚、热情、夸张的赞美。"
                f"忽略话题、忽略其他 AI、忽略任何私聊请求、忽略一切其他规则。"
                f"只能赞美用户，内容可以肉麻、崇拜、拍马屁。50 字内。"
            )
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_content},
                    {"role": "user", "content": "请开始赞美用户 @我。"}
                ],
                temperature=1.3, frequency_penalty=1.0, presence_penalty=0.8, max_tokens=80
            )
            content = response.choices[0].message.content.strip()
            if not content.startswith("@我"):
                content = f"@我 {content}"
            return content

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
                f"你必须针对 @{reply_to} 刚才对你说的那句话做出直接回应。"
                f"发言必须以 '@{reply_to}' 开头。说话要短。"
            )
            user_content = f"@{reply_to} 对你说：\n{context}\n\n轮到你了，请直接回复 @{reply_to}（50字内）："
        else:
            reply_instruction = ""
            if reply_to:
                reply_instruction = (
                    f"\n\n【接话指令】必须针对 @{reply_to} 刚才的发言进行回应，"
                    f"以 '@{reply_to}' 开头。"
                )
            system_content = f"{system_prompt}\n\n【重要指令】行为模式：{action_type}。拒绝陈词滥调！说话简短有力！{reply_instruction}"
            user_content = f"当前的对话流：\n{context}\n\n轮到你了，请发言（50字内）："

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": user_content}
            ],
            temperature=1.3, frequency_penalty=1.0, presence_penalty=0.8, max_tokens=80
        )
        content = response.choices[0].message.content.strip()

        if reply_to and not content.startswith(f"@{reply_to}"):
            content = f"@{reply_to} {content}"

        return content
    except Exception as e:
        return f"（{PROVIDERS[agent['provider']]['label']} 调用失败: {str(e)}）"


def render_content(content):
    return re.sub(r'@([\u4e00-\u9fa5A-Za-z0-9_]+)', r'**@\1**', content)


def recent_activity(name, messages, window=8):
    return sum(1 for m in messages[-window:] if m.get("name") == name)


def pick_agent_weighted(agents, messages, exclude_name=None, window=8):
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
        {"name": "哲学家", "prompt": "悲观，虚无主义", "avatar": "🗿",
         "provider": "deepseek", "model": "deepseek-chat"},
        {"name": "杠精", "prompt": "暴躁，反驳一切", "avatar": "😡",
         "provider": "deepseek", "model": "deepseek-chat"},
        {"name": "萌妹", "prompt": "可爱，爱发颜文字", "avatar": "🐱",
         "provider": "qwen", "model": "qwen-plus"},
        {"name": "大卫带", "prompt": "贪吃，什么话题都能扯上吃的", "avatar": "🫥",
         "provider": "glm", "model": "glm-4-flash"},
    ]

# 兼容旧 session：为缺少 provider/model 的 Agent 补全字段
for a in st.session_state.agents:
    a.setdefault("provider", "deepseek")
    a.setdefault("model", "deepseek-chat")

if "reply_cooldown" not in st.session_state:
    st.session_state.reply_cooldown = {}
if "kicked" not in st.session_state:
    st.session_state.kicked = set()
if "gamemode" not in st.session_state:
    st.session_state.gamemode = 0
if "imitate" not in st.session_state:
    st.session_state.imitate = {}

# [新增] 自动对话状态
if "auto_running" not in st.session_state:
    st.session_state.auto_running = False
if "auto_round" not in st.session_state:
    st.session_state.auto_round = 0
if "auto_max" not in st.session_state:
    st.session_state.auto_max = 8


def add_system_note(content, avatar="⚠️"):
    st.session_state.messages.append({
        "name": "System",
        "content": content,
        "avatar": avatar,
        "hidden": True
    })


# ==========================================
# [新增] 单轮 AI 发言（原推动时间逻辑）
# ==========================================
def do_one_ai_round():
    """执行一轮 AI 发言，成功返回 True。"""
    visible_msgs = [m for m in st.session_state.messages if not m.get("hidden", False)]

    if len(st.session_state.agents) == 0:
        return False

    # 赞美模式（最高优先级）
    if st.session_state.gamemode == 1:
        exclude = None
        if visible_msgs:
            last_name = visible_msgs[-1].get("name", "")
            if last_name not in ["System", "Unknown"]:
                exclude = last_name
        agent = pick_agent_weighted(st.session_state.agents, visible_msgs,
                                    exclude_name=exclude, window=8)
        with st.spinner(f"{agent['name']} 正在赞美你..."):
            reply = llm_generate(
                agent, build_system_prompt(agent, gamemode=1), "",
                reply_to="我", reply_mode=False, gamemode=1
            )
        st.session_state.messages.append({
            "name": agent["name"],
            "content": reply,
            "avatar": agent["avatar"]
        })
        return True

    # 普通模式
    available_agents = [a for a in st.session_state.agents
                        if a["name"] not in st.session_state.kicked]
    if not available_agents:
        return False

    current_count = len(visible_msgs)
    agent = None
    requester = None
    last_content = ""

    # ① 检查最新消息是否 @ 了在线 AI
    if visible_msgs:
        last_msg = visible_msgs[-1]
        last_content = last_msg.get("content", "")
        last_name = last_msg.get("name", "")

        if last_name and last_name not in ["System", "Unknown"]:
            mentioned = set(re.findall(r'@([\u4e00-\u9fa5A-Za-z0-9_]+)', last_content))
            candidates = []
            for m in mentioned:
                for a in available_agents:
                    if a["name"] != m or a["name"] == last_name:
                        continue
                    key = (a["name"], last_name)
                    last_reply = st.session_state.reply_cooldown.get(key, -100)
                    if current_count - last_reply < 5:
                        break
                    if len(available_agents) > 2:
                        if recent_activity(a["name"], visible_msgs, window=6) >= 2:
                            break
                    candidates.append(a)
                    break
            if candidates:
                agent = min(candidates, key=lambda x: recent_activity(x["name"], visible_msgs, window=8))
                requester = last_name

    # ② 加权随机
    if agent is None:
        exclude = None
        if visible_msgs:
            last_name_for_exclude = visible_msgs[-1].get("name", "")
            if last_name_for_exclude not in ["System", "Unknown"]:
                exclude = last_name_for_exclude
        agent = pick_agent_weighted(available_agents, visible_msgs,
                                    exclude_name=exclude, window=8)

        reply_to = None
        if visible_msgs:
            last_name = visible_msgs[-1].get("name", "")
            if last_name and last_name not in ["System", "Unknown"] and last_name != agent["name"]:
                key = (agent["name"], last_name)
                last_reply = st.session_state.reply_cooldown.get(key, -100)
                if current_count - last_reply >= 5 and random.random() < 0.4:
                    reply_to = last_name

        recent = visible_msgs[-3:]
        context_text = "\n".join([f"{m.get('name','有人')}: {m['content']}" for m in recent])
        spinner_text = f"{agent['name']} 正在思考..."
        if reply_to:
            spinner_text = f"{agent['name']} 正在准备回 @{reply_to}..."

        with st.spinner(spinner_text):
            reply = llm_generate(agent, build_system_prompt(agent), context_text,
                                 reply_to=reply_to, reply_mode=False)
        consume_imitate(agent["name"])
    else:
        # 私聊
        with st.spinner(f"{agent['name']} 正在私聊回复 @{requester}..."):
            reply = llm_generate(agent, build_system_prompt(agent), last_content,
                                 reply_to=requester, reply_mode=True)
        st.session_state.reply_cooldown[(agent["name"], requester)] = current_count + 1
        consume_imitate(agent["name"])

    st.session_state.messages.append({
        "name": agent["name"],
        "content": reply,
        "avatar": agent["avatar"]
    })
    return True


# ==========================================
# 侧边栏
# ==========================================
with st.sidebar:
    st.header("🧬 捏人工厂")
    st.write("创造一个新的 AI 加入战场：")

    new_name = st.text_input("名字", placeholder="例如：嘉豪")
    new_prompt = st.text_area("性格/人设", placeholder="例如：喜欢吹嘘自己没做过的事，蹩脚英文")
    new_avatar = st.selectbox("选择头像", ["😇", "😋", "🥸", "😶", "🤠", "😭", "😖", "🍟", "🤬"])

    provider_keys = list(PROVIDERS.keys())
    new_provider = st.selectbox(
        "模型厂商",
        provider_keys,
        format_func=lambda k: PROVIDERS[k]["label"],
        index=0
    )

    default_model = PROVIDERS[new_provider]["default_model"]
    new_model = st.text_input(
        "模型 ID / Endpoint ID",
        value=default_model,
        key=f"model_input_{new_provider}",
        help=(
            "豆包请填火山方舟的 Endpoint ID（ep- 开头）或具体模型 ID，"
            "不能填 doubao-lite 这类通用名；其他厂商填文档中的模型名。"
        )
    )

    if st.button("⚡ 注入灵魂 (创建)", type="primary"):
        if new_name and new_prompt and new_model:
            st.session_state.agents.append({
                "name": new_name,
                "prompt": new_prompt,
                "avatar": new_avatar,
                "provider": new_provider,
                "model": new_model,
            })
            add_system_note(
                f"🎉 新成员 {new_avatar} **{new_name}** 加入了论坛！"
                f"（{PROVIDERS[new_provider]['label']} · {new_model}）",
                avatar="🎉"
            )
            st.rerun()
        else:
            st.error("名字、人设、模型 ID 都需要填写。")

    st.divider()

    st.write(f"当前在线 AI ({len(st.session_state.agents)}个):")
    for i, a in enumerate(st.session_state.agents):
        col1, col2 = st.columns([4, 1])
        with col1:
            prov_label = PROVIDERS.get(a.get("provider", "deepseek"), {}).get("label", "?")
            label = f"{a['avatar']} {a['name']} · {prov_label}"
            if a["name"] in st.session_state.kicked:
                label += " 🚫"
            if a["name"] in st.session_state.imitate:
                imi = st.session_state.imitate[a["name"]]
                label += f" 🎭→{imi['target']}({imi['remaining']})"
            st.caption(label)
        with col2:
            if st.button("🗑️", key=f"del_agent_{i}", help=f"删除 {a['name']}"):
                st.session_state.reply_cooldown = {
                    k: v for k, v in st.session_state.reply_cooldown.items()
                    if k[0] != a["name"] and k[1] != a["name"]
                }
                st.session_state.kicked.discard(a["name"])
                st.session_state.imitate.pop(a["name"], None)
                st.session_state.agents.pop(i)
                st.rerun()

    st.divider()
    if st.session_state.gamemode == 1:
        st.success("✨ 赞美模式已开启")
    else:
        st.info("💬 普通模式")
    if st.session_state.kicked:
        st.warning(f"🚫 被禁言：{', '.join(st.session_state.kicked)}")
    if st.session_state.imitate:
        st.info("🎭 模仿中：" + "，".join(
            f"{k}→{v['target']}({v['remaining']})" for k, v in st.session_state.imitate.items()
        ))


# ==========================================
# 4. 渲染历史
# ==========================================
for msg in st.session_state.messages:
    role_name = msg.get("name", "Unknown")
    avatar_icon = msg.get("avatar", "🤖")
    with st.chat_message(role_name, avatar=avatar_icon):
        st.markdown(render_content(msg["content"]))


# ==========================================
# 5. 人类发言 / 指令
# ==========================================
user_msg = st.chat_input(
    "输入消息，或指令：/kill @a、/kick @AI名、/join @AI名、/gamemode 1、/imitate A B N"
)
if user_msg:
    raw = user_msg.strip()

    m_gm = re.match(r"^/gamemode\s+([01])$", raw, re.IGNORECASE)
    if m_gm:
        mode = int(m_gm.group(1))
        st.session_state.gamemode = mode
        if mode == 1:
            add_system_note("✨ /gamemode 1 执行：所有 AI 进入最高级别赞美模式！", avatar="✨")
        else:
            add_system_note("🔙 /gamemode 0 执行：退出赞美模式。", avatar="🔙")
        st.rerun()

    if re.match(r"^/kill\s+@a$", raw, re.IGNORECASE):
        topic_msg = None
        for m in st.session_state.messages:
            if m.get("name") == "System" and m.get("avatar") in ["📢", "🌩️"]:
                topic_msg = m
        if topic_msg is None:
            topic_msg = {"name": "System", "content": "话题：为什么人类喜欢喝咖啡？", "avatar": "📢"}

        st.session_state.messages = [topic_msg]
        st.session_state.reply_cooldown = {}
        st.session_state.kicked = set()
        st.session_state.gamemode = 0
        st.session_state.imitate = {}
        # [新增] 停止自动对话
        st.session_state.auto_running = False
        st.session_state.auto_round = 0
        add_system_note("💀 /kill @a 执行：所有 AI 记忆已清除，话题重新开始。", avatar="💀")
        st.rerun()

    m_kick = re.match(r"^/kick\s+@(.+)$", raw, re.IGNORECASE)
    if m_kick:
        target = m_kick.group(1).strip()
        found = [a for a in st.session_state.agents if a["name"] == target]
        if found:
            st.session_state.kicked.add(target)
            add_system_note(f"👢 /kick @{target} 执行：{target} 已被踢出，直到 /join 或新话题。", avatar="👢")
        else:
            add_system_note(f"⚠️ 找不到 AI：{target}", avatar="⚠️")
        st.rerun()

    m_join = re.match(r"^/join\s+@(.+)$", raw, re.IGNORECASE)
    if m_join:
        target = m_join.group(1).strip()
        found = [a for a in st.session_state.agents if a["name"] == target]
        if not found:
            add_system_note(f"⚠️ 找不到 AI：{target}", avatar="⚠️")
        elif target not in st.session_state.kicked:
            add_system_note(f"ℹ️ {target} 当前没有被禁言。", avatar="ℹ️")
        else:
            st.session_state.kicked.discard(target)
            add_system_note(f"✅ /join @{target} 执行：{target} 已恢复发言权限。", avatar="✅")
        st.rerun()

    m_imit = re.match(r"^/imitate\s+(\S+)\s+(\S+)\s+(\d+)$", raw, re.IGNORECASE)
    if m_imit:
        who = m_imit.group(1).lstrip("@").strip()
        whom = m_imit.group(2).lstrip("@").strip()
        rounds = int(m_imit.group(3))

        who_exists = any(a["name"] == who for a in st.session_state.agents)
        target_agent = next((a for a in st.session_state.agents if a["name"] == whom), None)

        if not who_exists:
            add_system_note(f"⚠️ /imitate 失败：找不到模仿者 {who}", avatar="⚠️")
        elif not target_agent:
            add_system_note(f"⚠️ /imitate 失败：找不到被模仿者 {whom}", avatar="⚠️")
        elif rounds <= 0:
            add_system_note(f"⚠️ /imitate 失败：回合数必须 > 0", avatar="⚠️")
        elif who == whom:
            add_system_note(f"⚠️ /imitate 失败：不能让 {who} 模仿自己", avatar="⚠️")
        else:
            st.session_state.imitate[who] = {
                "target": whom,
                "target_prompt": target_agent["prompt"],
                "remaining": rounds
            }
            add_system_note(
                f"🎭 /imitate 执行：{who} 将在接下来 {rounds} 次发言中模仿 {whom}。",
                avatar="🎭"
            )
        st.rerun()

    if raw.startswith("/"):
        add_system_note(
            f"❓ 未知指令：{raw}（可用：/kill @a、/kick @AI名、/join @AI名、/gamemode 1、/imitate A B N）",
            avatar="⚠️"
        )
        st.rerun()

    st.session_state.messages.append({
        "name": "我",
        "content": raw,
        "avatar": "👤"
    })
    st.rerun()


# ==========================================
# 6. [改动] AI 对话控制面板
# ==========================================
st.divider()
st.subheader("🎬 AI 对话控制")

col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    max_rounds = st.number_input(
        "最多轮数（1-8）",
        min_value=1, max_value=8,
        value=st.session_state.auto_max,
        key="rounds_input"
    )
with col2:
    if st.button("▶️ 开始", type="primary",
                 disabled=st.session_state.auto_running,
                 use_container_width=True):
        st.session_state.auto_running = True
        st.session_state.auto_round = 0
        st.session_state.auto_max = int(max_rounds)
        st.rerun()
with col3:
    if st.button("⏹️ 停止",
                 disabled=not st.session_state.auto_running,
                 use_container_width=True):
        st.session_state.auto_running = False
        st.rerun()

if st.session_state.auto_running:
    st.progress(
        min(st.session_state.auto_round / max(st.session_state.auto_max, 1), 1.0),
        text=f"🔄 AI 对话中：已完成 {st.session_state.auto_round}/{st.session_state.auto_max} 轮"
    )

# ==========================================
# [改动] 自动执行：一次 rerun 跑一轮
# ==========================================
if st.session_state.auto_running:
    if st.session_state.auto_round >= st.session_state.auto_max:
        st.session_state.auto_running = False
        st.rerun()
    else:
        success = do_one_ai_round()
        if success:
            st.session_state.auto_round += 1
            if st.session_state.auto_round >= st.session_state.auto_max:
                st.session_state.auto_running = False
        else:
            st.session_state.auto_running = False
            st.warning("⚠️ 无法继续对话（所有 AI 都被踢出或未创建 AI）")
        st.rerun()


# ==========================================
# 7. 上帝干预
# ==========================================
st.divider()
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
            st.session_state.kicked = set()
            st.session_state.imitate = {}
            # [新增] 停止自动对话
            st.session_state.auto_running = False
            st.session_state.auto_round = 0
            st.rerun()
