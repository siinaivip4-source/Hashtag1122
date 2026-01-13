import streamlit as st
import pandas as pd
from PIL import Image
import io
import torch
import clip
import os

# --- 1. CẤU HÌNH GIAO DIỆN (CSS CHO ĐẸP NHƯ BẢN LOCAL) ---
st.set_page_config(page_title="AI Master V8 - Visual Edit", page_icon="🔮", layout="wide")

st.markdown("""
    <style>
    div[data-testid="stImage"] {border-radius: 10px; overflow: hidden; border: 1px solid #4ea8de;}
    .stButton>button {width: 100%; border-radius: 8px; font-weight: bold;}
    div.stSelectbox > label {font-weight: bold; color: #ffbd45;}
    </style>
""", unsafe_allow_html=True)

st.title("🔮 AI MASTER V8 - VISUAL CLOUD")
st.markdown("### 1. Upload Ảnh -> 2. AI Xử lý -> 3. Sửa Tag trực tiếp -> 4. Xuất Excel")

# --- 2. DATASET CHUẨN ---
STYLES = [
    "2D", "3D", "Cute", "Animeart", "Realism", 
    "Aesthetic", "Cool", "Fantasy", "Comic", "Horror", 
    "Cyberpunk", "Lofi", "Minimalism", "Digitalart", "Cinematic", 
    "Pixelart", "Scifi", "Vangoghart"
]

COLORS = [
    "Black", "White", "Blackandwhite", "Red", "Yellow", 
    "Blue", "Green", "Pink", "Orange", "Pastel", 
    "Hologram", "Vintage", "Colorful", "Neutral", "Light", 
    "Dark", "Warm", "Cold", "Neon", "Gradient", 
    "Purple", "Brown", "Grey"
]

# --- 3. LOAD MODEL (GIỮ NGUYÊN TRÍ TUỆ V6) ---
@st.cache_resource
def load_engine():
    device = "cpu" # Cloud dùng CPU
    model, preprocess = clip.load("ViT-B/32", device=device)
    
    # Prompt Engineering V6
    s_prompts = []
    for s in STYLES:
        if s == "Cool": txt = "cool, stylish, badass attitude, swagger"
        elif s == "Cute": txt = "cute, adorable, chibi, kawaii"
        elif s == "3D": txt = "3D CGI render, blender, unreal engine"
        elif s == "Realism": txt = "photorealistic, 4k photograph, detailed texture"
        elif s == "Animeart": txt = "anime style, japanese manga"
        else: txt = f"a {s} style artwork"
        s_prompts.append(txt)

    c_prompts = []
    for c in COLORS:
        if c == "Colorful": txt = "colorful, many different colors, chaotic rainbow"
        elif c == "Hologram": txt = "holographic, iridescent, cd reflection"
        elif c == "Neon": txt = "glowing neon lights, cyber colors"
        elif c == "Pastel": txt = "pastel colors, soft macaron colors"
        else: txt = f"dominant color is {c}"
        c_prompts.append(txt)
    
    s_vectors = clip.tokenize(s_prompts).to(device)
    c_vectors = clip.tokenize(c_prompts).to(device)
    
    with torch.no_grad():
        s_feat = model.encode_text(s_vectors)
        c_feat = model.encode_text(c_vectors)
        s_feat /= s_feat.norm(dim=-1, keepdim=True)
        c_feat /= c_feat.norm(dim=-1, keepdim=True)
        
    return model, preprocess, s_feat, c_feat, device

try:
    with st.spinner("⏳ Đang triệu hồi AI (Chờ chút nhé)..."):
        model, preprocess, s_feat, c_feat, device = load_engine()
except Exception as e:
    st.error(f"Lỗi Model: {e}")
    st.stop()

# --- 4. LOGIC XỬ LÝ ---
def predict_image(image):
    # Convert RGB nếu cần
    if image.mode != "RGB": image = image.convert("RGB")
    
    image_input = preprocess(image).unsqueeze(0).to(device)
    with torch.no_grad():
        img_feat = model.encode_image(image_input)
        img_feat /= img_feat.norm(dim=-1, keepdim=True)
        
    s_idx = (100.0 * img_feat @ s_feat.T).softmax(dim=-1).argmax().item()
    c_idx = (100.0 * img_feat @ c_feat.T).softmax(dim=-1).argmax().item()
    return STYLES[s_idx], COLORS[c_idx]

# --- 5. GIAO DIỆN CHÍNH ---

# Sidebar Control
with st.sidebar:
    st.header("⚙️ Cấu hình")
    start_idx = st.number_input("STT Bắt đầu:", value=101, step=1)
    
    # Nút Upload
    uploaded_files = st.file_uploader(
        "Upload ảnh (Max 50):", 
        type=['png','jpg','jpeg','webp'], 
        accept_multiple_files=True
    )
    
    analyze_btn = st.button("▶️ PHÂN TÍCH ẢNH", type="primary")
    
    st.markdown("---")
    if st.button("🔄 Reset Tất cả"):
        st.session_state.clear()
        st.rerun()

# State Management (Lưu dữ liệu để sửa đổi)
if "results" not in st.session_state:
    st.session_state["results"] = []

# Xử lý khi bấm nút Phân tích
if analyze_btn and uploaded_files:
    temp_results = []
    progress = st.progress(0)
    status = st.empty()
    
    for i, file in enumerate(uploaded_files):
        status.text(f"Đang soi: {file.name}")
        try:
            # Đọc ảnh vào RAM
            image_bytes = file.getvalue()
            img = Image.open(io.BytesIO(image_bytes))
            
            # AI đoán
            style, color = predict_image(img)
            
            # Lưu vào danh sách (Lưu cả ảnh để hiển thị)
            temp_results.append({
                "id": i, # ID tạm
                "filename": file.name,
                "image_obj": img, # Lưu object ảnh để hiển thị lại
                "style": style,
                "color": color
            })
        except:
            pass
        progress.progress((i+1)/len(uploaded_files))
    
    st.session_state["results"] = temp_results
    status.success("✅ Đã xong! Mời Sư huynh duyệt bên phải ->")

# --- 6. HIỂN THỊ GRID VIEW & EDIT (GIỐNG PHƯƠNG ÁN A) ---
if st.session_state["results"]:
    
    # Nút Xuất Excel nằm trên cùng cho tiện
    c1, c2 = st.columns([3, 1])
    with c1:
        st.subheader(f"📝 KẾT QUẢ ({len(st.session_state['results'])} ảnh)")
    with c2:
        # Chuẩn bị dữ liệu Excel
        export_data = []
        for i, item in enumerate(st.session_state["results"]):
            export_data.append({
                "STT": start_idx + i,
                "Tên ảnh": item["filename"],
                "Hashtag Style": item["style"],
                "Hashtag Color": item["color"]
            })
        df = pd.DataFrame(export_data)
        
        # Buffer Excel
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False)
            
        st.download_button(
            label="💾 TẢI EXCEL VỀ MÁY",
            data=buffer.getvalue(),
            file_name="hashtags_v8_final.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary"
        )

    st.divider()

    # TẠO GRID 3 CỘT (VISUAL EDITOR)
    cols = st.columns(3)
    
    for i, item in enumerate(st.session_state["results"]):
        with cols[i % 3]: # Chia bài vào 3 cột
            with st.container(border=True):
                # Hiện ảnh
                st.image(item["image_obj"], use_container_width=True)
                st.caption(f"{start_idx + i}. {item['filename']}")
                
                # Dropdown chỉnh sửa (Real-time update state)
                new_s = st.selectbox(
                    "Style", 
                    STYLES, 
                    index=STYLES.index(item["style"]), 
                    key=f"s_{i}"
                )
                new_c = st.selectbox(
                    "Color", 
                    COLORS, 
                    index=COLORS.index(item["color"]), 
                    key=f"c_{i}"
                )
                
                # Cập nhật ngược lại vào data gốc
                st.session_state["results"][i]["style"] = new_s
                st.session_state["results"][i]["color"] = new_c

elif not uploaded_files:
    st.info("👈 Mời Sư huynh upload ảnh bên menu trái để bắt đầu!")
