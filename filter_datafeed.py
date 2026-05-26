import pandas as pd
import json
import os

def filter_shopee_datafeed():
    DATAFEED_URL = "http://datafeed.accesstrade.me/shopee.vn.csv"
    
    # BỘ TỪ KHÓA SIÊU RỘNG ĐỂ QUÉT ĐƯỢC TOÀN BỘ CÁC NGÀNH HÀNG HOT NHẤT
    KEYWORDS = [
        "phím", "chuột", "tai nghe", "gaming", "sạc", "cáp", "loa", "điện thoại", "máy tính",
        "áo", "quần", "váy", "giày", "dép", "balo", "túi", "ví", "thắt lưng",
        "son", "kem", "serum", "mụn", "nước hoa", "sữa tắm", "dầu gội",
        "bánh", "kẹo", "khô bò", "mực", "gạch", "ốp", "đèn", "kệ", "tủ"
    ]
    
    print("🚀 Đang kết nối và tải lướt siêu dữ liệu từ Accesstrade...")
    products_list = []
    
    try:
        # Đọc thử 5 dòng để map tên cột
        preview_df = pd.read_csv(DATAFEED_URL, sep=',', nrows=5, on_bad_lines='skip')
        
        name_col = 'name' if 'name' in preview_df.columns else preview_df.columns[1]
        price_col = 'discount' if 'discount' in preview_df.columns else ('price' if 'price' in preview_df.columns else preview_df.columns[3])
        image_col = 'image' if 'image' in preview_df.columns else preview_df.columns[5]
        link_col = 'url' if 'url' in preview_df.columns else preview_df.columns[2]

        print(f"🎯 Ánh xạ cột thành công -> Name: {name_col} | Price: {price_col} | Link: {link_col}")

        # Đọc dữ liệu theo cụm lớn hơn (100,000 dòng/cụm) để quét nhanh hơn
        chunk_size = 100000
        for chunk in pd.read_csv(DATAFEED_URL, sep=',', chunksize=chunk_size, on_bad_lines='skip'):
            
            chunk[name_col] = chunk[name_col].astype(str)
            
            # Quét qua danh sách từ khóa rộng
            for keyword in KEYWORDS:
                filtered_chunk = chunk[chunk[name_col].str.contains(keyword, case=False, na=False)]
                
                for _, row in filtered_chunk.iterrows():
                    products_list.append({
                        "name": str(row[name_col]).strip(),
                        "price_current": str(row[price_col]).strip(),
                        "image": str(row[image_col]).strip(),
                        "link": str(row[link_col]).strip()
                    })
                    
                # Nếu kho đã chứa đủ 20,000 sản phẩm thì chủ động dừng lại để file không bị quá nặng
                if len(products_list) >= 20000:
                    break
            if len(products_list) >= 20000:
                break
                    
        print(f"✅ Đã gom đủ hàng cho đại siêu thị! Tổng cộng: {len(products_list)} sản phẩm.")
        
        # Cắt chính xác lấy 20,000 sản phẩm đa dạng nhất
        final_products = products_list[:20000]
        
        # Ghi đè vào file JSON ở thư mục gốc
        current_dir = os.path.dirname(os.path.abspath(__file__))
        output_file = os.path.join(current_dir, "shopee_products.json")
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(final_products, f, ensure_ascii=False, indent=4)
            
        print(f"🎉 Đã xuất file JSON thành công!")
        # Đổi dung lượng ra MB cho bạn dễ hình dung
        file_size_mb = os.path.getsize(output_file) / (1024 * 1024)
        print(f"📂 Kích thước file JSON hiện tại: {file_size_mb:.2f} MB.")
        
    except Exception as e:
        print(f"❌ Lỗi xử lý: {str(e)}")
        raise e

if __name__ == "__main__":
    filter_shopee_datafeed()
