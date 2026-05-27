import os
import json
import pandas as pd
import requests

def convert_to_affiliate_links(urls, api_key):
    """
    Gửi loạt link sang API AccessTrade để chuyển thành link affiliate.
    API cho phép gửi danh sách link để giảm số lần request.
    """
    api_url = "https://api.accesstrade.vn/v1/links"
    headers = {
        "Authorization": f"Token {api_key}",
        "Content-Type": "application/json"
    }
    
    # Payload theo định dạng của AccessTrade API
    payload = {
        "urls": urls
    }
    
    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=15)
        if response.status_code == 200:
            result_data = response.json()
            # Trả về danh sách short_link hoặc product_link theo đúng thứ tự
            return [item.get("short_link") for item in result_data]
        else:
            print(f"⚠️ API lỗi (Status {response.status_code}): {response.text}")
            return urls # Nếu lỗi thì trả lại link gốc để không mất data
    except Exception as e:
        print(f"⚠️ Lỗi kết nối API: {e}")
        return urls

def filter_shopee_datafeed():
    DATAFEED_URL = "http://datafeed.accesstrade.me/shopee.vn.csv"
    API_KEY = "5ZYbgIAp67OIsN4VXQS0lQkCNvbU2zj-"
    
    print("🚀 Đang kết nối và tải datafeed từ Shopee...")
    
    try:
        # 1. Đọc thử 5 dòng để map tên cột tự động
        preview_df = pd.read_csv(DATAFEED_URL, sep=',', nrows=5, on_bad_lines='skip')
        
        name_col = 'name' if 'name' in preview_df.columns else preview_df.columns[1]
        price_col = 'price' if 'price' in preview_df.columns else preview_df.columns[3]
        image_col = 'image' if 'image' in preview_df.columns else preview_df.columns[5]
        link_col = 'url' if 'url' in preview_df.columns else preview_df.columns[2]

        print(f"🎯 Ánh xạ cột thành công -> Name: {name_col} | Price: {price_col} | Link: {link_col}")

        # 2. Đọc toàn bộ dữ liệu theo dạng chunk nhưng dùng xử lý vector của Pandas cho nhanh
        chunk_size = 50000
        collected_dfs = []
        total_products = 0
        
        for chunk in pd.read_csv(DATAFEED_URL, sep=',', chunksize=chunk_size, on_bad_lines='skip'):
            # Làm sạch dữ liệu rác trực tiếp bằng pandas (nhanh hơn vạn lần vòng lặp for)
            chunk = chunk.dropna(subset=[name_col, link_col])
            chunk = chunk[(chunk[name_col].astype(str).str.strip() != "") & (chunk[name_col].astype(str) != "nan")]
            chunk = chunk[(chunk[link_col].astype(str).str.strip() != "") & (chunk[link_col].astype(str) != "nan")]
            
            collected_dfs.append(chunk[[name_col, price_col, image_col, link_col]])
            total_products += len(chunk)
            
            if total_products >= 30000:
                break
                
        # Gộp các chunk lại và cắt đúng 30,000 sản phẩm sạch
        main_df = pd.concat(collected_dfs, ignore_index=True).head(30000)
        print(f"📥 Đã lọc xong {len(main_df)} sản phẩm gốc. Chuẩn bị chuyển đổi link affiliate...")

        # 3. Tiến hành gom nhóm 50 link để gọi API một lần (Tránh bị khóa IP/Rate Limit)
        origin_links = main_df[link_col].astype(str).str.strip().tolist()
        affiliate_links = []
        batch_size = 50  # AccessTrade khuyên dùng từ 10-50 link mỗi request
        
        print(f"🔄 Đang chuyển đổi link qua API AccessTrade (Mỗi đợt {batch_size} links)...")
        for i in range(0, len(origin_links), batch_size):
            batch = origin_links[i:i+batch_size]
            converted_batch = convert_to_affiliate_links(batch, API_KEY)
            affiliate_links.extend(converted_batch)
            
            if (i + batch_size) % 500 == 0 or (i + batch_size) >= len(origin_links):
                print(f"⏳ Đã chuyển đổi: {min(i + batch_size, len(origin_links))}/{len(origin_links)} links")

        # Cập nhật lại cột link trong DataFrame
        main_df['affiliate_link'] = affiliate_links

        # 4. Chuyển cấu trúc sang JSON và lưu file
        products_list = []
        for _, row in main_df.iterrows():
            products_list.append({
                "name": str(row[name_col]).strip(),
                "price_current": str(row[price_col]).strip() if pd.notna(row[price_col]) else "0",
                "image": str(row[image_col]).strip() if pd.notna(row[image_col]) else "N/A",
                "link": row['affiliate_link'] # Link đã được gắn mã tiếp thị
            })

        current_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in locals() else os.getcwd()
        output_file = os.path.join(current_dir, "shopee_products.json")
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(products_list, f, ensure_ascii=False, indent=4)
            
        print(f"🎉 Đã cập nhật file shopee_products.json thành công!")
        file_size_mb = os.path.getsize(output_file) / (1024 * 1024)
        print(f"📂 Kích thước file JSON: {file_size_mb:.2f} MB.")
        
    except Exception as e:
        print(f"❌ Lỗi xử lý: {str(e)}")
        raise e

if __name__ == "__main__":
    filter_shopee_datafeed()
