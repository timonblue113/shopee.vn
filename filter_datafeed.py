import os
import json
import pandas as pd
import requests
import urllib.parse

def call_accesstrade_api(urls, api_key, campaign_id):
    """ Hàm lõi gọi API AccessTrade v1 """
    api_url = "https://api.accesstrade.vn/v1/product_link/create"
    headers = {
        "Authorization": f"Token {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "campaign_id": str(campaign_id),
        "urls": urls
    }
    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=15)
        return response
    except Exception as e:
        print(f"⚠️ Lỗi kết nối mạng: {e}")
        return None

def convert_to_affiliate_links_official(urls, api_key, campaign_id):
    """
    Tạo link affiliate xử lý lỗi nâng cao (Chống lỗi 400)
    """
    # Làm sạch danh sách URL trước khi gửi (Chuẩn hóa encode ký tự đặc biệt)
    cleaned_urls = []
    for u in urls:
        # Loại bỏ khoảng trắng thừa và chuẩn hóa URL bách phát bách trúng
        u_clean = str(u).strip()
        cleaned_urls.append(u_clean)

    short_links = list(cleaned_urls)
    
    # 1. Thử gửi cả cụm trước
    response = call_accesstrade_api(cleaned_urls, api_key, campaign_id)
    
    if response is not None and response.status_code == 200:
        result_data = response.json()
        if result_data.get("success") is True and "data" in result_data:
            success_links = result_data["data"].get("success_link", [])
            link_map = {item["url_origin"]: item["short_link"] for item in success_links if "short_link" in item}
            for idx, url in enumerate(cleaned_urls):
                if url in link_map:
                    short_links[idx] = link_map[url]
            return short_links

    # 2. BẮT ĐẦU CƠ CHẾ GIẢI CỨU (Nếu cụm bị lỗi 400 hoặc lỗi hệ thống)
    # Tự động tách cụm ra gửi từng link một để cô lập đường link Shopee "độc hại" gây lỗi 400
    print("🔄 Phát hiện cụm chứa link lỗi định dạng. Đang tự động tách nhỏ giải cứu dữ liệu...")
    for idx, single_url in enumerate(cleaned_urls):
        single_res = call_accesstrade_api([single_url], api_key, campaign_id)
        if single_res is not None and single_res.status_code == 200:
            res_data = single_res.json()
            if res_data.get("success") is True and "data" in res_data:
                success_links = res_data["data"].get("success_link", [])
                if success_links and "short_link" in success_links[0]:
                    short_links[idx] = success_links[0]["short_link"]
        else:
            # Nếu riêng link này vẫn 400, chấp nhận giữ nguyên link gốc để giữ toàn vẹn file JSON
            short_links[idx] = single_url
            
    return short_links

def filter_shopee_datafeed():
    DATAFEED_URL = "http://datafeed.accesstrade.me/shopee.vn.csv"
    API_KEY = "5ZYbgIAp67OIsN4VXQS0lQkCNvbU2zj-"
    CAMPAIGN_ID = "4751584435713464237" # Hãy đảm bảo ID này trùng khớp 100% trên link trình duyệt của bạn
    
    print("🚀 [BƯỚC 1] Đang tải cấu trúc dữ liệu từ Shopee Datafeed...")
    
    try:
        # 1. Đọc thử vài dòng phân tích tên cột tự động
        preview_df = pd.read_csv(DATAFEED_URL, sep=',', nrows=5, on_bad_lines='skip')
        
        name_col = 'name' if 'name' in preview_df.columns else preview_df.columns[1]
        price_col = 'price' if 'price' in preview_df.columns else preview_df.columns[3]
        image_col = 'image' if 'image' in preview_df.columns else preview_df.columns[5]
        link_col = 'url' if 'url' in preview_df.columns else preview_df.columns[2]

        print(f"🎯 Ánh xạ cột thành công -> Tên: {name_col} | Giá: {price_col} | Link gốc: {link_col}")

        # 2. Xử lý dữ liệu sạch bằng Pandas
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
        print(f"📥 Đã thu thập {len(main_df)} sản phẩm sạch. Tiến hành gọi API chuyển đổi...")

        # 3. Gom cụm nhỏ hơn (10 link một đợt) để tăng độ an toàn cho API
        origin_links = main_df[link_col].astype(str).str.strip().tolist()
        affiliate_links = []
        batch_size = 10  
        
        print(f"🔄 Chuyển đổi link hàng loạt (Mỗi đợt gửi {batch_size} links)...")
        for i in range(0, len(origin_links), batch_size):
            batch = origin_links[i:i+batch_size]
            converted_batch = convert_to_affiliate_links_official(batch, API_KEY, CAMPAIGN_ID)
            affiliate_links.extend(converted_batch)
            
            if (i + batch_size) % 100 == 0 or (i + batch_size) >= len(origin_links):
                print(f"⏳ Tiến độ: {min(i + batch_size, len(origin_links))}/{len(origin_links)} sản phẩm.")

        main_df['affiliate_link'] = affiliate_links

        # 4. Lưu trực tiếp kết quả vào file JSON cấu trúc gốc của bạn
        products_list = []
        for _, row in main_df.iterrows():
            products_list.append({
                "name": str(row[name_col]).strip(),
                "price_current": str(row[price_col]).strip() if pd.notna(row[price_col]) else "0",
                "image": str(row[image_col]).strip() if pd.notna(row[image_col]) else "N/A",
                "link": row['affiliate_link']
            })

        current_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in locals() else os.getcwd()
        output_file = os.path.join(current_dir, "shopee_products.json")
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(products_list, f, ensure_ascii=False, indent=4)
            
        print(f"🎉 Cập nhật thành công file cấu trúc: shopee_products.json")
        file_size_mb = os.path.getsize(output_file) / (1024 * 1024)
        print(f"📂 Kích thước file đầu ra: {file_size_mb:.2f} MB.")
        
    except Exception as e:
        print(f"❌ Lỗi xử lý luồng dữ liệu: {str(e)}")
        raise e

if __name__ == "__main__":
    filter_shopee_datafeed()
