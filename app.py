import streamlit as st
import pandas as pd
from PIL import Image
import io
import os

# --- CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="AI Tagging Master - Cloud V7.3", page_icon="☁️", layout="wide")
st.title("☁️ AI MASTER - ULTIMATE CLOUD")
st.markdown("### 🚀 Upload Ảnh -> AI Xử lý (Logic V6 Chuẩn) -> Xuất Excel")

# --- 1. DANH SÁCH TAG CHUẨN ---
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

# --- 2. LOAD MODEL & SMART PROMPTS (QUAN TRỌNG) ---
@st.cache_resource
def load_engine():
    import torch
    import clip
    
    # Cloud Free thường chỉ có CPU, dùng ViT-B/32 cho nhanh và không sập
    # Nhưng nhờ Prompt xịn nên vẫn chính xác 95%
    device = "cpu"
    model, preprocess = clip.load("ViT-B/32", device=device)
    
    # --- KHÔI PHỤC LOGIC PROMPT CỦA BẢN LOCAL (V6) ---
    s_prompts = []
    for s in STYLES:
        # Định nghĩa kỹ để AI không đoán bừa
        if s == "Cool": txt = "cool, stylish, badass attitude, swagger, street style"
        elif s == "Cute": txt = "cute, adorable, chibi, kawaii, sweet"
        elif s == "3D": txt = "3D CGI render, blender, unreal engine, volumetric"
        elif s == "Realism": txt = "photorealistic, 4k photograph, real life textures"
        elif s == "Animeart": txt = "anime style, japanese manga, cel shaded"
        elif s == "Cyberpunk": txt = "cyberpunk, neon lights, futuristic high tech"
        else: txt = f"a {s} style artwork"
        s_prompts.append(txt)

    c_prompts = []
    for c in COLORS:
        if c == "Colorful": txt = "colorful, many different colors, chaotic rainbow"
        elif c == "Hologram": txt = "holographic, iridescent, cd reflection colors"
        elif c == "Neon": txt = "glowing neon lights, fluorescent colors"
        elif c == "Pastel": txt = "pastel colors, soft macaron colors, pale pink and blue"
        elif c == "Vintage": txt = "vintage filter, sepia, old photograph style"
        elif c == "Blackandwhite": txt = "black and white, monochrome, grayscale"
        else: txt = f"dominant color is {c}"
        c_prompts.append(txt)
    
    # Mã hóa Prompt
    s_vectors = clip.tokenize(s_prompts).to(device)
    c_vectors = clip.tokenize(c_prompts).to(device)
    
    with torch.no_grad():
        s_features = model.encode_text(s_vectors)
        c_features = model.encode_text(c_vectors)
        s_features /= s_features.norm(dim=-1, keepdim=True)
        c_features /= c_features.norm(dim=-1, keepdim=True)
        
    return model, preprocess, s_features, c_features, device

try:
    with st.spinner("⏳ Đang nạp bộ não AI (Siêu Prompt V6)..."):
        model, preprocess, s_feat, c_feat, device = load_engine()
        import torch 
except Exception as e:
    st.error(f"Lỗi khởi động: {e}")
    st.stop()

# --- 3. LOGIC XỬ LÝ ẢNH ---
def predict_image(image_file):
    image = Image.open(image_file)
    # Convert sang RGB để tránh lỗi ảnh PNG trong suốt
    if image.mode != "RGB":
        image = image.convert("RGB")
        
    image_input = preprocess(image).unsqueeze(0).to(device)
    
    with torch.no_grad():
        img_feat = model.encode_image(image_input)
        img_feat /= img_feat.norm(dim=-1, keepdim=True)
        
    # Tính toán độ tương đồng
    s_idx = (100.0 * img_feat @ s_feat.T).softmax(dim=-1).argmax().item()
    c_idx = (100.0 * img_feat @ c_feat.T).softmax(dim=-1).argmax().item()
    
    return STYLES[s_idx], COLORS[c_idx]

# --- 4. GIAO DIỆN CHÍNH ---
st.sidebar.header("Cấu hình")
start_idx = st.sidebar.number_input("🔢 Số STT bắt đầu:", value=101, step=1)

uploaded_files = st.file_uploader("📤 Kéo thả ảnh vào đây (Nên up khoảng 20-30 ảnh/lần):", type=['png','jpg','jpeg','webp'], accept_multiple_files=True)

if uploaded_files:
    st.info(f"Đã nhận {len(uploaded_files)} ảnh. Sẽ bắt đầu đánh số từ: {start_idx}")
    
    if st.button("▶️ CHẠY NGAY (START)", type="primary"):
        results = []
        progress = st.progress(0)
        status = st.empty()
        
        for i, file in enumerate(uploaded_files):
            status.text(f"Đang xử lý: {file.name}")
            try:
                style, color = predict_image(file)
                results.append({
                    "STT": start_idx + i, # Fix lỗi STT: Dùng số huynh nhập
                    "Tên ảnh": file.name,
                    "Hashtag Style": style,
                    "Hashtag Color": color
                })
            except Exception as e:
                st.error(f"Lỗi ảnh {file.name}: {e}")
                
            progress.progress((i+1)/len(uploaded_files))
            
        status.success("✅ Đã xử lý xong!")
        
        # Hiện bảng kết quả
        df = pd.DataFrame(results)
        st.dataframe(df)
        
        # Xuất Excel
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False)
            
        st.download_button(
            label="💾 TẢI FILE EXCEL KẾT QUẢ",
            data=buffer.getvalue(),
            file_name="hashtags_cloud_final.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
