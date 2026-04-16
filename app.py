import streamlit as st
import pandas as pd
from groq import Groq
import io

# Initialize Client
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

st.set_page_config(page_title="Product Mapper", layout="wide")
st.title("📦 Product Variant Mapper")

if 'final_df' not in st.session_state:
    st.session_state.final_df = pd.DataFrame()
if 'last_index' not in st.session_state:
    st.session_state.last_index = 0

uploaded_file = st.file_uploader("Upload your Brand-Sorted CSV", type="csv")

if uploaded_file:
    input_df = pd.read_csv(uploaded_file)
    total_rows = len(input_df)
    
    st.write(f"Processed {st.session_state.last_index} / {total_rows} products.")
    progress_bar = st.progress(st.session_state.last_index / total_rows if total_rows > 0 else 0)

    if st.button("Run / Resume Analysis"):
        batch_size = 15 
        
        for i in range(st.session_state.last_index, total_rows, batch_size):
            batch = input_df.iloc[i : i + batch_size]
            data_string = ""
            for _, row in batch.iterrows():
                data_string += f"SKU: {row['SKU']}, Label: {row['Label']}, Brand: {row['Brand']}\n"

            try:
                chat_completion = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[
                        {"role": "system", "content": "Return ONLY SKU|PARENT_SKU. If unique, leave PARENT_SKU blank."},
                        {"role": "user", "content": data_string}
                    ]
                )

                raw_response = chat_completion.choices[0].message.content
                mapping_dict = {}
                
                # Safer parsing loop
                for line in raw_response.split('\n'):
                    if "|" in line:
                        parts = line.split("|")
                        if len(parts) == 2:
                            mapping_dict[parts[0].strip()] = parts[1].strip()

                current_batch = batch.copy()
                current_batch['Variant of'] = current_batch['SKU'].map(mapping_dict)

                st.session_state.final_df = pd.concat([st.session_state.final_df, current_batch], ignore_index=True)
                st.session_state.last_index += len(current_batch)
                progress_bar.progress(st.session_state.last_index / total_rows)
                
            except Exception as e:
                st.error(f"Error at row {i}: {e}")
                break

    if not st.session_state.final_df.empty:
        st.subheader("Mapped Data Preview")
        st.dataframe(st.session_state.final_df.head(100))
        
        csv_buffer = io.BytesIO()
        st.session_state.final_df.to_csv(csv_buffer, index=False)
        st.download_button(
            label="Download Mapped CSV",
            data=csv_buffer.getvalue(),
            file_name="mapped_products.csv",
            mime="text/csv"
        )
