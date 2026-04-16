import streamlit as st
import pandas as pd
from groq import Groq
import io

# Initialize Client
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

st.set_page_config(page_title="Product Mapper", layout="wide")
st.title("📦 Product Variant Mapper")
st.info("Sorted by Brand? Good. This script will now process your items in batches.")

# Initialize session state to store our progress
if 'final_df' not in st.session_state:
    st.session_state.final_df = pd.DataFrame()
if 'last_index' not in st.session_state:
    st.session_state.last_index = 0

uploaded_file = st.file_uploader("Upload your Brand-Sorted CSV", type="csv")

if uploaded_file:
    # Read original data
    input_df = pd.read_csv(uploaded_file)
    total_rows = len(input_df)
    
    # Progress tracking UI
    progress_bar = st.progress(st.session_state.last_index / total_rows if total_rows > 0 else 0)
    st.write(f"Processed {st.session_state.last_index} / {total_rows} products.")

    if st.button("Run / Resume Analysis"):
        batch_size = 15 
        
        for i in range(st.session_state.last_index, total_rows, batch_size):
            batch = input_df.iloc[i : i + batch_size]
            
            # Prepare the data for the AI
            data_string = ""
            for _, row in batch.iterrows():
                data_string += f"SKU: {row['SKU']}, Label: {row['Label']}, Brand: {row['Brand']}\n"

            try:
                # Using the '8b' model which has higher free-tier limits
                chat_completion = client.chat.completions.create(
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a data assistant. Group products that are variants of the same item. Pick one SKU as the Parent. Return ONLY a list in this format: SKU|PARENT_SKU. If it is a parent or unique, leave PARENT_SKU blank. Example: SKU123|SKU100"
                        },
