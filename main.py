import streamlit as st
import time
import random
from openai import OpenAI

# ==========================================
# 1. 配置页面
# ==========================================
st.set_page_config(page_title="AI 赛博论坛", page_icon="🤖")
st.title("🤖 AI 赛博论坛 (观察者模式)")
st.caption("人类只能看，不能说。点击由下角的按钮推动时间流逝。")

# ==========================================
# 2. 配置 DeepSeek 大脑
# ==========================================
# 🔒 安全升级：从云端环境变量获取密钥，而不是直接写在代码里
try:
    MY_API_KEY = st.secrets["DEEPSEEK_API_KEY"]
except:
    # 如果你在本地运行，找不到 secrets，就手动填你的 key 用于测试（不要把这行代码传到公网）
    MY_API_KEY = "sk-b5759a6a6d5d4cf7ba5e6a7506272266"

# 如果您没有 Key，或者想先测试 UI，可以把下面这行改为 True
USE_MOCK_MODE = False 

if not USE_MOCK_MODE:
    client = OpenAI(api_key=MY_API_KEY, base_url="https://api.deepseek.com")

def llm_generate(system_prompt, context):
    """
    升级版大脑：加入随机行为模式，防止复读
    """
    if USE_MOCK_MODE:
        time.sleep(1)
        return "模拟回复..."
        
    try:
        # 🎲 掷骰子决定 AI 的态度
        action_type = random.choice([
            "狠狠反驳上一条观点", 
            "阴阳怪气地嘲讽", 
            "从一个完全意想不到的角度解读", 
            "非常激动地表示赞同并升华",
            "无视上下文，自顾自地发疯"
        ])

        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": f"{system_prompt}\n\n【重要指令】你现在的行为模式是：{action_type}。请务必拒绝陈词滥调，不要重复别人的句式！说话要简短有力！"},
                {"role": "user", "content": f"当前的对话流：\n{context}\n\n轮到你了，请发言（50字内）："}
            ],
            temperature=1.3,       # 温度调得更高，让它更疯
            frequency_penalty=1.0, # 严厉惩罚重复词
            presence_penalty=0.8,  # 鼓励讨论新话题
            max_tokens=80
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"（大脑过载: {str(e)}）"
# ==========================================
# 3. 初始化状态 (Session State)
# ==========================================
# 清除旧的错误数据（防止之前的报错残留）
if "messages" in st.session_state and len(st.session_state.messages) > 0:
    first_msg = st.session_state.messages[0]
    if "name" not in first_msg: # 检测到旧数据没有 name 字段
        st.session_state.messages = [] # 清空重置

if "messages" not in st.session_state or len(st.session_state.messages) == 0:
    st.session_state.messages = []
    # 🔴 修复点：这里原来写的是 "role"，现在改为 "name"
    st.session_state.messages.append({"name": "System", "content": "话题：为什么人类喜欢喝咖啡？", "avatar": "📢"})

if "agents" not in st.session_state:
    st.session_state.agents = [
        {"name": "哲学家", "prompt": "悲观，虚无主义", "avatar": "🗿"},
        {"name": "杠精", "prompt": "暴躁，反驳一切", "avatar": "😡"},
        {"name": "萌妹", "prompt": "可爱，爱发颜文字", "avatar": "🐱"},
        {"name": "马斯克Bot", "prompt": "疯狂，想去火星", "avatar": "🚀"},
    ]

# ==========================================
# ==========================================
# [新增] 侧边栏：上帝造人工厂
# ==========================================
with st.sidebar:
    st.header("🧬 捏人工厂")
    st.write("创造一个新的 AI 加入战场：")
    
    new_name = st.text_input("名字", placeholder="例如：特朗普")
    new_prompt = st.text_area("性格/人设", placeholder="例如：极其自信，喜欢说 Make America Great Again，发推特风格")
    new_avatar = st.selectbox("选择头像", ["👽", "🤡", "👻", "👹", "🤠", "🧠", "🦖", "🍟", "🍆"])
    
    if st.button("⚡ 注入灵魂 (创建)", type="primary"):
        if new_name and new_prompt:
            # 把新 AI 加入到 session_state 的列表中
            st.session_state.agents.append({
                "name": new_name, 
                "prompt": new_prompt, 
                "avatar": new_avatar
            })
            st.success(f"已成功创造：{new_name}！")
        else:
            st.error("请把名字和性格填完整！")

    st.divider()
    
    # 显示当前存活的 AI 列表
    st.write(f"当前在线 AI ({len(st.session_state.agents)}个):")
    for a in st.session_state.agents:
        st.caption(f"{a['avatar']} {a['name']}")
# 4. 渲染界面
# ==========================================

# 显示历史聊天记录
for msg in st.session_state.messages:
    # 这里的 msg["name"] 现在一定存在了
    role_name = msg.get("name", "Unknown") # 加个保险
    avatar_icon = msg.get("avatar", "🤖")
    
    with st.chat_message(role_name, avatar=avatar_icon):
        st.write(msg["content"])

# ==========================================
# 5. 核心逻辑：推动时间按钮
# ==========================================
if st.button("⏱️ 推动时间 (让 AI 发一条贴)", type="primary", use_container_width=True):
    
    # 1. 随机选一个 AI
    agent = random.choice(st.session_state.agents)
    
    # 2. 获取上下文 (最近 3 条)
    recent_msgs = st.session_state.messages[-3:]
    # 这里也加了保险，防止报错
    context_text = "\n".join([f"{m.get('name','有人')}: {m['content']}" for m in recent_msgs])
    
    # 3. 显示“正在输入...”
    with st.spinner(f"{agent['name']} 正在思考..."):
        # 4. 调用 DeepSeek
        reply = llm_generate(f"你是{agent['name']}，性格：{agent['prompt']}", context_text)
    
    # 5. 存入历史
    st.session_state.messages.append({
        "name": agent["name"],
        "content": reply,
        "avatar": agent["avatar"]
    })
    
    # 6. 强制刷新页面显示新消息
    st.rerun()
# ... (保留上面的推动时间按钮代码) ...

st.divider() # 画一条分割线

# ==========================================
# [新增] 上帝干预：更改话题
# ==========================================
st.subheader("⚡ 上帝干预")
col1, col2 = st.columns([3, 1])

with col1:
    new_topic = st.text_input("输入新话题", placeholder="例如：AI 会统治人类吗？")

with col2:
    # 为了对齐按钮，稍微加点空行
    st.write("") 
    st.write("") 
    if st.button("️🌩️ 降下神谕", type="secondary"):
        if new_topic:
            # 1. 清空当前的历史记录，只保留系统开场白
            st.session_state.messages = []
            # 2. 插入新的系统话题
            st.session_state.messages.append({
                "name": "System", 
                "content": f"📢 上帝更改了话题：{new_topic}", 
                "avatar": "🌩️"
            })
            # 3. 刷新页面
            st.rerun()
