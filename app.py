import streamlit as st
import pandas as pd
from PIL import Image
import io
import os
import sys

# --- CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="AI Tagging Master - Cloud", page_icon="☁️", layout="wide")
st.title("☁️ AI MASTER - PHIÊN BẢN PUBLIC")
st.markdown("### 🚀 Tải ảnh lên -> AI tự gắn thẻ -> Xuất Excel")

# --- LIST DATA CHUẨN (THEO ẢNH 1) ---
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

# --- LOAD MODEL (CACHE) ---
@st.cache_resource
def load_engine():
    # Cài đặt thư viện AI
    import torch
    import clip
    
    device = "cpu" # Trên Cloud miễn phí thường chỉ có CPU, chạy vẫn ổn
    model, preprocess = clip.load("ViT-B/32", device=device) # Dùng bản nhẹ cho Cloud đỡ sập
    
    # Chuẩn bị Prompt
    s_vectors = clip.tokenize([f"a {s} style artwork" for s in STYLES]).to(device)
    c_vectors = clip.tokenize([f"dominant color is {c}" for c in COLORS]).to(device)
    
    with torch.no_grad():
        s_features = model.encode_text(s_vectors)
        c_features = model.encode_text(c_vectors)
        s_features /= s_features.norm(dim=-1, keepdim=True)
        c_features /= c_features.norm(dim=-1, keepdim=True)
        
    return model, preprocess, s_features, c_features, device

try:
    with st.spinner("⏳ Đang khởi động AI trên Mây (Chờ chút nhé)..."):
        model, preprocess, s_feat, c_feat, device = load_engine()
        import torch # Re-import local scope
except Exception as e:
    st.error(f"Lỗi khởi động: {e}")
    st.stop()

# --- LOGIC XỬ LÝ ---
def predict_image(image_file):
    image = Image.open(image_file)
    image_input = preprocess(image).unsqueeze(0).to(device)
    
    with torch.no_grad():
        img_feat = model.encode_image(image_input)
        img_feat /= img_feat.norm(dim=-1, keepdim=True)
        
    # Tính toán
    s_idx = (100.0 * img_feat @ s_feat.T).softmax(dim=-1).argmax().item()
    c_idx = (100.0 * img_feat @ c_feat.T).softmax(dim=-1).argmax().item()
    
    return STYLES[s_idx], COLORS[c_idx]

# --- GIAO DIỆN CHÍNH ---
uploaded_files = st.file_uploader("📤 Kéo thả ảnh vào đây (Max 50 ảnh/lần):", type=['png','jpg','jpeg','webp'], accept_multiple_files=True)

if uploaded_files:
    st.info(f"Đã nhận {len(uploaded_files)} ảnh. Nhấn nút dưới để bắt đầu!")
    
    if st.button("▶️ CHẠY NGAY", type="primary"):
        results = []
        progress = st.progress(0)
        
        for i, file in enumerate(uploaded_files):
            try:
                style, color = predict_image(file)
                results.append({
                    "STT": 101 + i,
                    "Tên ảnh": file.name,
                    "Hashtag Style": style,
                    "Hashtag Color": color
                })
            except:
                pass # Bỏ qua ảnh lỗi
            progress.progress((i+1)/len(uploaded_files))
            
        st.success("✅ Đã xử lý xong!")
        
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