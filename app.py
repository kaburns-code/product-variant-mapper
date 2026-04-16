import streamlit as st
import pandas as pd
from groq import Groq
import os

# Initialize Groq Client
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

st.title("🛍️ Product Variant Mapper (Groq Edition)")

uploaded_file = st.file_uploader("Upload your Product CSV", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.write(f"Loaded {len(df)} products.")

    if st.button("Analyze Variants"):
        results = []
        # We process in batches of 20 to keep the AI focused
        batch_size = 20 
        
        progress_bar = st.progress(0)
        status_text = st.empty()

        for i in range(0, len(df), batch_size):
            batch = df.iloc[i:i+batch_size]
            
            # Construct the prompt using Label and Brand
            product_list = "\n".join([f"SKU: {row['SKU']}, Label: {row['Label']}, Brand: {row['Brand']}" for _, row in batch.iterrows()])
            
            prompt = f"""
            Act as a product database expert. Below is a list of products.
            Identify which products are variants of each other (e.g., same item but different size, color, count, or dosage).
            
            RULES:
            1. For each group of variants, pick one 'Parent SKU' (the most standard version).
            2. Return a CSV-style list: SKU, Variant_Of
            3. If a product is unique or is the Parent itself, leave 'Variant_Of' blank.
            4. ONLY return the CSV rows. No prose.

            PRODUCTS:
            {product_list}
            """

            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Simple parsing of the AI's CSV response
            output = response.choices[0].message.content
            # (In a production app, you'd add more robust parsing here)
            st.text(output) 
            
            progress_bar.progress((i + batch_size) / len(df))
        
        st.success("Analysis Complete!")
