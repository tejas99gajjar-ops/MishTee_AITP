import gradio as gr
import pandas as pd
import requests
from supabase import create_client, Client

# --- 1. INITIALIZATION & ASSETS ---
SUPABASE_URL = "https://ctbxbptwddistpnvenlp.supabase.co"
SUPABASE_KEY = "https://ctbxbptwddistpnvenlp.supabase.co" 
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

LOGO_URL = "https://github.com/tejas99gajjar-ops/MishTee_AITP/blob/main/MishTee_Logo_1.png?raw=true"
STYLE_URL = "https://raw.githubusercontent.com/tejas99gajjar-ops/MishTee_AITP/refs/heads/main/style.py"

# Fetch CSS from GitHub style.py
try:
    response = requests.get(STYLE_URL)
    mishtee_css = response.text if response.status_code == 200 else ""
except Exception:
    mishtee_css = ""

# --- 2. CORE FUNCTIONS ---

def get_trending_products():
    """Fetches top 4 best selling products based on quantity."""
    try:
        res = supabase.table("orders").select("qty_kg, products(sweet_name, variant_type, price_per_kg)").execute()
        if not res.data:
            return pd.DataFrame(columns=['Sweet Name', 'Variant', 'Price (₹/kg)', 'Total Sold (kg)'])

        raw_df = pd.DataFrame(res.data)
        raw_df['Sweet Name'] = raw_df['products'].apply(lambda x: x['sweet_name'])
        raw_df['Variant'] = raw_df['products'].apply(lambda x: x['variant_type'])
        raw_df['Price'] = raw_df['products'].apply(lambda x: x['price_per_kg'])
        
        trending = raw_df.groupby(['Sweet Name', 'Variant', 'Price'])['qty_kg'].sum().reset_index()
        trending = trending.sort_values(by='qty_kg', ascending=False).head(4)
        trending.columns = ['Sweet Name', 'Variant', 'Price (₹/kg)', 'Total Sold (kg)']
        return trending
    except Exception:
        return pd.DataFrame(columns=['Sweet Name', 'Variant', 'Price (₹/kg)', 'Total Sold (kg)'])

def handle_login(phone_number):
    """Executes the login logic: Greeting + Order History + Trending."""
    if not phone_number or len(phone_number) < 10:
        return "Please enter a valid 10-digit phone number.", pd.DataFrame(), pd.DataFrame()

    try:
        cust_res = supabase.table("customers").select("full_name").eq("phone", phone_number).execute()
        
        if not cust_res.data:
            greeting = "### Welcome!\nPlease register at our store to see your magic moments!"
            history_df = pd.DataFrame()
        else:
            customer_name = cust_res.data[0]['full_name']
            greeting = f"### Namaste, {customer_name} ji!\n**Great to see you again.**"

            order_res = supabase.table("orders").select(
                "order_id, order_date, qty_kg, order_value_inr, status, products(sweet_name)"
            ).eq("cust_phone", phone_number).execute()

            if order_res.data:
                orders_df = pd.DataFrame(order_res.data)
                orders_df['Product'] = orders_df['products'].apply(lambda x: x['sweet_name'] if x else "Unknown")
                history_df = orders_df[['order_id', 'order_date', 'Product', 'qty_kg', 'order_value_inr', 'status']]
                history_df.columns = ['Order ID', 'Date', 'Item', 'Qty (kg)', 'Amount (₹)', 'Status']
            else:
                history_df = pd.DataFrame(columns=['Order ID', 'Date', 'Item', 'Qty (kg)', 'Amount (₹)', 'Status'])

        trending_df = get_trending_products()
        return greeting, history_df, trending_df

    except Exception as e:
        return f"System Error: {str(e)}", pd.DataFrame(), pd.DataFrame()

# --- 3. UI LAYOUT ---

# Re-applying css to gr.Blocks as your environment requires it here.
# Removed gr.Spacer and replaced with gr.HTML for vertical spacing.
with gr.Blocks(css=mishtee_css, title="MishTee-Magic | Customer App") as demo:
    
    # Header Section
    with gr.Row():
        with gr.Column(scale=1):
            gr.Image(LOGO_URL, show_label=False, container=False, height=100, width=100)
        with gr.Column(scale=4):
            gr.Markdown("# MishTee-Magic")
            gr.Markdown("*[Purity and Health]*")

    gr.HTML("<br>") 

    # Login Section
    with gr.Row(variant="panel"):
        with gr.Column(scale=2):
            phone_input = gr.Textbox(label="Mobile Number", placeholder="Enter 9xxxxxxxxx")
            login_btn = gr.Button("Enter the Magic", variant="primary")
        with gr.Column(scale=3):
            greeting_output = gr.Markdown("### Welcome\nPlease login to view your history.")

    gr.HTML("<br>") 

    # Data Tables Section
    with gr.Tabs():
        with gr.TabItem("✨ Trending Today"):
            trending_table = gr.Dataframe(interactive=False)
            
        with gr.TabItem("📜 My Order History"):
            history_table = gr.Dataframe(interactive=False)

    # --- 4. EVENT TRIGGERS ---
    login_btn.click(
        fn=handle_login,
        inputs=[phone_input],
        outputs=[greeting_output, history_table, trending_table]
    )

# --- 5. LAUNCH ---
if __name__ == "__main__":
    # Standard launch without the 'css' argument
    demo.launch()
