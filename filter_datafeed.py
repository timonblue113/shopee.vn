import os
import json
import pandas as pd
import requests

def convert_to_affiliate_links_v2(urls, api_key):
    """
    Gửi loạt link sang API v2 để tạo link rút gọn chuẩn cho chiến dịch Shopee Smartlink.
    """
    # Endpoint chuẩn V2 dành cho các chiến dịch tạo link/smartlink
    api_url = "https://api.accesstrade.vn/v2/links"
    
    headers = {
        "Authorization": f"Token {api_key}",
        "Content-Type": "application/json"
    }
    
    # Cấu trúc Body chuẩn theo tài liệu API v2 của AccessTrade
    payload = {
        "urls": urls
    }
    
    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=15)
        if response.status_code == 200:
            result_data = response.json()
            
            # Khởi tạo mảng kết quả
            short_links = []
            
            # API V2 trả về một dict chứa key "data", trong đó là mảng các link đã xử lý
            if isinstance(result_data, dict) and "data" in result_data:
                items = result_data["data"]
                for idx, item in enumerate(items):
                    if isinstance(item, dict) and "short_link" in item:
                        short_links.append(item["short_link"])
                    else:
                        # Nếu phần tử đó lỗi, trả về link gốc tương ứng để không mất data
                        short_links.append(urls[idx])
            else:
                # Nếu cấu trúc trả về lạ, giữ nguyên link gốc
                return urls
                
            return short_links
        else:
            print(f"⚠️ API v2 báo lỗi (Status {response.status_code}): {response.text}")
            return urls  # Lỗi thì giữ link gốc để script tiếp tục chạy
    except Exception as e:
        print(f"⚠️ Lỗi kết nối API v2: {e}")
        return urls

def filter_shopee_datafeed():
    DATAFEED_URL = "http://datafeed.accesstrade.me/shopee.vn.csv"
    API_KEY = "5ZYbgIAp67OIsN4VXQS0lQkCNvbU2zj-"
    
    print("🚀 [Bước 1] Đang kết nối và tải dữ liệu từ Shopee Datafeed...")
    
    try:
        # 1. Đọc thử vài dòng để tự động map tên cột
        preview_df = pd.read_csv(DATAFEED_URL, sep=',', nrows=5, on_bad_lines='skip')
        
        name_col = 'name' if 'name' in preview_df.columns else preview_df.columns[1]
        price_col = 'price' if 'price' in preview_df.columns else preview_df.columns[3]
        image_col = 'image' if 'image' in preview_df.columns else preview_df.columns[5]
        link_col = 'url' if 'url' in preview_df.columns else preview_df.columns[2]

        print(f"🎯 Ánh xạ cột thành công -> Tên: {name_col} | Giá: {price_col} | Link gốc: {link_col}")

        # 2. Đọc và lọc sạch dữ liệu bằng Pandas (bỏ qua hàng trống/lỗi)
        chunk_size = 50000
        collected_dfs = []
        total_products = 0
        
        for chunk in pd.read_csv(DATAFEED_URL, sep=',', chunksize=chunk_size, on_bad_lines='skip'):
            chunk = chunk.dropna(subset=[name_col, link_col])
            chunk = chunk[(chunk[name_col].astype(str).str.strip() != "") & (chunk[name_col].astype(str) != "nan")]
            chunk = chunk[(chunk[link_col].astype(str).str.strip() != "") & (chunk[link_col].astype(str) != "nan")]
            
            collected_dfs.append(chunk[[name_col, price_col, image_col, link_col]])
            total_products += len(chunk)
            
            if total_products >= 30000:
                break
                
        main_df = pd.concat(collected_dfs, ignore_index=True).head(30000)
        print(f"📥 Đã gom sạch {len(main_df)} sản phẩm. Tiến hành kết nối API v2 để gắn mã tiếp thị...")

        # 3. Gom cụm 50 link gửi đi một lượt (Tránh Rate Limit / Quá tải hệ thống)
        origin_links = main_df[link_col].astype(str).str.strip().tolist()
        affiliate_links = []
        batch_size = 50  
        
        print(f"🔄 Đang tạo link Affiliate qua AccessTrade V2 (Mỗi đợt {batch_size} links)...")
        for i in range(0, len(origin_links), batch_size):
            batch = origin_links[i:i+batch_size]
            converted_batch = convert_to_affiliate_links_v2(batch, API_KEY)
            affiliate_links.extend(converted_batch)
            
            # Cập nhật tiến độ mỗi 500 links
            if (i + batch_size) % 500 == 0 or (i + batch_size) >= len(origin_links):
                print(f"⏳ Tiến độ xử lý: {min(i + batch_size, len(origin_links))}/{len(origin_links)} sản phẩm.")

        # Thêm cột link tiếp thị liên kết vào DataFrame
        main_df['affiliate_link'] = affiliate_links

        # 4. Trích xuất cấu trúc cuối cùng và ghi đè vào JSON
        products_list = []
        for _, row in main_df.iterrows():
            products_list.append({
                "name": str(row[name_col]).strip(),
                "price_current": str(row[price_col]).strip() if pd.notna(row[price_col]) else "0",
                "image": str(row[image_col]).strip() if pd.notna(row[image_col]) else "N/A",
                "link": row['affiliate_link']  # Link đã được đổi thành link affiliate của bạn
            })

        current_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in locals() else os.getcwd()
        output_file = os.path.join(current_dir, "shopee_products.json")
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(products_list, f, ensure_ascii=False, indent=4)
            
        print(f"🎉 Xuất file JSON thành công!")
        file_size_mb = os.path.getsize(output_file) / (1024 * 1024)
        print(f"📂 File lưu tại: {output_file} (Dung lượng: {file_size_mb:.2f} MB).")
        
    except Exception as e:
        print(f"❌ Lỗi xử lý: {str(e)}")
        raise e

if __name__ == "__main__":
    filter_shopee_datafeed()
