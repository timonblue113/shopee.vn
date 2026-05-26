import pandas as pd
import json
import os

def filter_shopee_datafeed():
    DATAFEED_URL = "http://datafeed.accesstrade.me/shopee.vn.csv"
    
    print("🚀 Đang kết nối và hốt thẳng 30,000 sản phẩm đầu tiên từ datafeed...")
    products_list = []
    
    try:
        # Đọc thử 5 dòng để map tên cột tự động
        preview_df = pd.read_csv(DATAFEED_URL, sep=',', nrows=5, on_bad_lines='skip')
        
        name_col = 'name' if 'name' in preview_df.columns else preview_df.columns[1]
        price_col = 'discount' if 'discount' in preview_df.columns else ('price' if 'price' in preview_df.columns else preview_df.columns[3])
        image_col = 'image' if 'image' in preview_df.columns else preview_df.columns[5]
        link_col = 'url' if 'url' in preview_df.columns else preview_df.columns[2]

        print(f"🎯 Ánh xạ cột thành công -> Name: {name_col} | Price: {price_col} | Link: {link_col}")

        # Cho con bot đọc file theo từng cụm lớn
        chunk_size = 50000
        for chunk in pd.read_csv(DATAFEED_URL, sep=',', chunksize=chunk_size, on_bad_lines='skip'):
            
            # Ép kiểu dữ liệu an toàn
            chunk[name_col] = chunk[name_col].astype(str)
            
            # Không lọc key nữa, duyệt qua từng dòng một của chunk và nhét vào kho luôn
            for _, row in chunk.iterrows():
                p_name = str(row[name_col]).strip()
                p_link = str(row[link_col]).strip()
                
                # Né các dòng rác không có tên hoặc không có link mua hàng
                if p_name == "" or p_name == "nan" or p_link == "" or p_link == "nan":
                    continue
                    
                products_list.append({
                    "name": p_name,
                    "price_current": str(row[price_col]).strip() if price_col in chunk.columns else "0",
                    "image": str(row[image_col]).strip() if image_col in chunk.columns else "N/A",
                    "link": p_link
                })
                
                # Kiểm tra nếu đủ 30,000 sản phẩm thì ngắt xe xúc luôn
                if len(products_list) >= 30000:
                    break
                    
            if len(products_list) >= 30000:
                break
                    
        print(f"✅ Đã gom đủ: {len(products_list)} sản phẩm đầu tiên của sàn!")
        
        # Ghi đè vào file JSON ở thư mục gốc
        current_dir = os.path.dirname(os.path.abspath(__file__))
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
