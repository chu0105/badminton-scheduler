import streamlit as st
import os
import sys

# 確保路徑正確
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from badminton_player_test import BadmintonApp 

# 設定網頁標題
st.set_page_config(page_title="羽球即時排程系統", layout="wide")

# 初始化後端邏輯
if 'app' not in st.session_state:
    st.session_state.app = BadmintonApp()
app = st.session_state.app

# --- 管理員密碼設定 ---
ADMIN_PASSWORD = "666"  # 你可以改成任何你想要的密碼

# 初始化權限狀態
if 'is_admin' not in st.session_state:
    st.session_state.is_admin = False

st.title("🏸 羽球即時排程補位系統")

# --- 側邊欄：登入與點名 ---
with st.sidebar:
    st.header("🔑 權限控制")
    pwd_input = st.text_input("輸入管理員密碼", type="password")
    
    # 密碼檢查邏輯
    if pwd_input == ADMIN_PASSWORD:
        st.session_state.is_admin = True
        st.success("✅ 管理員身分已確認")
    else:
        st.session_state.is_admin = False
        if pwd_input:
            st.error("❌ 密碼錯誤")

    st.divider()
    st.header("👥 今日出席名單")
    all_names = [p['name'] for p in app.players]
    active_names = st.multiselect("勾選今日到場球員", all_names, default=all_names)
    
    # 只有管理員能看到「設定」與「初始排程按鈕」
    if st.session_state.is_admin:
        st.header("⚙️ 場地設定")
        num_courts = st.number_input("開放場地數量", min_value=1, max_value=6, value=1)
        if st.button("🚀 初始全場排程 (重排)", type="primary"):
            courts, matches = app.get_scheduled_matches(active_names, num_courts)
            st.session_state.current_matches = matches
            st.rerun()
    else:
        st.info("ℹ️ 非管理員僅供查閱")

# --- 主畫面：即時對戰區 ---
if 'current_matches' in st.session_state and st.session_state.current_matches:
    st.subheader("🏟️ 正在進行中的場次")
    cols = st.columns(len(st.session_state.current_matches))
    
    for i, (t1, t2) in enumerate(st.session_state.current_matches):
        with cols[i]:
            st.info(f"### 場地 {i+1}")
            t1_names = [p['name'] for p in t1]
            t2_names = [p['name'] for p in t2]
            
            st.markdown(f"**A 隊**：\n{t1[0]['name']} & {t1[1]['name']}")
            st.markdown(f"**B 隊**：\n{t2[0]['name']} & {t2[1]['name']}")
            
            # --- 權限限制：只有管理員能回報勝負 ---
            if st.session_state.is_admin:
                st.divider()
                btn_a, btn_b = st.columns(2)
                if btn_a.button(f"A 勝", key=f"win_a_{i}"):
                    app.report_result(t1_names, t2_names)
                    others = []
                    for idx, m in enumerate(st.session_state.current_matches):
                        if idx != i: others.extend([p['name'] for p in m[0] + m[1]])
                    new_match = app.get_single_court_match(active_names, others)
                    if new_match: st.session_state.current_matches[i] = new_match
                    st.rerun()

                if btn_b.button(f"B 勝", key=f"win_b_{i}"):
                    app.report_result(t2_names, t1_names)
                    others = []
                    for idx, m in enumerate(st.session_state.current_matches):
                        if idx != i: others.extend([p['name'] for p in m[0] + m[1]])
                    new_match = app.get_single_court_match(active_names, others)
                    if new_match: st.session_state.current_matches[i] = new_match
                    st.rerun()
            else:
                st.write("🏁 賽事進行中")

# --- 資訊顯示區 ---
st.divider()
tab1, tab2 = st.tabs(["📊 球員數據", "💤 休息名單"])

with tab1:
    st.dataframe(app.players, use_container_width=True)

with tab2:
    if 'current_matches' in st.session_state:
        on_court = []
        for m in st.session_state.current_matches: on_court.extend([p['name'] for p in m[0] + m[1]])
        waiting = [p for p in app.players if p['name'] in active_names and p['name'] not in on_court]
        for p in waiting:
            st.write(f"⏳ **{p['name']}** (已等 {p['wait_round']} 輪，已打 {p['play_count']} 場)")

# --- 管理員專屬：新增與手動調整 (放在最下面) ---
if st.session_state.is_admin:
    st.divider()
    with st.expander("🛠️ 管理員進階設定 (新增/修改球員)"):
        c1, c2 = st.columns(2)
        with c1:
            st.write("### ➕ 新增球員")
            n_name = st.text_input("姓名")
            n_level = st.slider("初始能力", 10.0, 14.0, 11.0, 0.1)
            n_gender = st.selectbox("性別", ["M", "F"])
            if st.button("確認新增"):
                if n_name: 
                    app.add_player(n_name, n_level, n_gender)
                    st.rerun()
        with c2:
            st.write("### 📝 手動修正")
            e_name = st.selectbox("修改對象", [""] + [p['name'] for p in app.players])
            if e_name:
                p_data = next(p for p in app.players if p['name'] == e_name)
                new_l = st.number_input("等級調整", value=p_data['level'], step=0.1)
                if st.button("儲存修改"):
                    p_data['level'] = round(new_l, 2)
                    app.save_data()
                    st.rerun()