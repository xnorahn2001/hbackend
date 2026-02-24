import streamlit as st
import streamlit.components.v1 as components
import os
import base64

# --- Page Config ---
st.set_page_config(
    page_title="Hayat Pro System", 
    layout="wide", 
    page_icon="image/Hyat.png",
    initial_sidebar_state="collapsed"
)

# --- Remove Streamlit's Default Padding/Styles ---
st.markdown("""
    <style>
        .block-container {
            padding-top: 0rem !important;
            padding-bottom: 0rem !important;
            padding-left: 0rem !important;
            padding-right: 0rem !important;
            max-width: 100% !important;
        }
        header[data-testid="stHeader"] { display: none; }
        footer { display: none; }
        div[data-testid="stToolbar"] { display: none; }
        iframe {
            display: block; 
            width: 100vw; 
            height: 100vh; 
            border: none;
        }
    </style>
""", unsafe_allow_html=True)

def get_image_base64(file_path):
    """Reads an image and returns a base64 encoded string."""
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            data = f.read()
            encoded = base64.b64encode(data).decode()
            # Determine mime type roughly
            if file_path.lower().endswith('.png'):
                mime = "image/png"
            elif file_path.lower().endswith('.jpg') or file_path.lower().endswith('.jpeg'):
                mime = "image/jpeg"
            else:
                mime = "image/png"
            return f"data:{mime};base64,{encoded}"
    return None

# --- Load & Render the HTML Dashboard ---
def load_dashboard():
    # Path to the HTML file
    html_path = "hayat_dashboard.html"
    # Path to the image
    image_path = "image/Hyat.png"
    
    if os.path.exists(html_path):
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
            
        # Get Base64 Image
        img_b64 = get_image_base64(image_path)
        
        if img_b64:
            # Replace the relative path in HTML with the Base64 string
            html_content = html_content.replace('src="image/Hyat.png"', f'src="{img_b64}"')
            html_content = html_content.replace("src='image/Hyat.png'", f"src='{img_b64}'") 
        
        # Display the HTML
        components.html(html_content, height=1000, scrolling=True)
    else:
        st.error(f"Dashboard HTML file not found at {html_path}.")

if __name__ == "__main__":
    load_dashboard()