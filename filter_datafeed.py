import pandas as pd
import json
import os

def filter_shopee_datafeed():
    DATAFEED_URL = "http://datafeed.accesstrade.me/shopee.vn.csv"
    
    # BỘ TỪ KHÓA ĐA DẠNG HƠN ĐỂ ĐẢM BẢO VÉT ĐỦ 30,000 SẢN PHẨM KHÔNG BỊ THIẾU
    KEYWORDS = [
        "phím", "chuột", "tai nghe", "gaming", "sạc", "cáp", "loa", "điện thoại", "máy tính", "vỏ",
        "áo", "quần", "váy", "giày", "dép", "balo", "túi", "ví", "thắt lưng", "mũ", "nón", "kính",
        "son", "kem", "serum", "mụn", "nước hoa", "sữa tắm", "dầu gội", "phấn", "tẩy trang",
        "bánh", "kẹo", "khô bò", "mực", "gạch", "ốp", "đèn", "kệ", "tủ", "bàn", "ghế", "gối", "nệm",
        "bình", "ly", "chén", "đũa", "muỗng", "nồi", "chảo", "thớt", "dao", "kéo", "lau nhà",
        "tã", "bỉm", "sữa", "đồ chơi", "xe", "vớ", "tất", "khăn", "khẩu trang", "pin", "led"
    ]
    
    print("🚀 Đang kết nối và tải lướt siêu dữ liệu từ Accesstrade...")
    products_list = []
    
    try:
        # Đọc thử 5 dòng để map tên cột tự động
        preview_df = pd.read_csv(DATAFEED_URL, sep=',', nrows=5, on_bad_lines='skip')
        
        name_col = 'name' if 'name' in preview_df.columns else preview_df.columns[1]
        price_col = 'discount' if 'discount' in preview_df.columns else ('price' if 'price' in preview_df.columns else preview_df.columns[3])
        image_col = 'image' if 'image' in preview_df.columns else preview_df.columns[5]
        link_col = 'url' if 'url' in preview_df.columns else preview_df.columns[2]

        print(f"🎯 Ánh xạ cột thành công -> Name: {name_col} | Price: {price_col} | Link: {link_col}")

        # Đọc dữ liệu theo cụm lớn (100,000 dòng/cụm) để máy ảo xử lý siêu tốc
        chunk_size = 100000
        for chunk in pd.read_csv(DATAFEED_URL, sep=',', chunksize=chunk_size, on_bad_lines='skip'):
            
            chunk[name_col] = chunk[name_col].astype(str)
            
            # Quét qua danh sách từ khóa rộng để bốc hàng
            for keyword in KEYWORDS:
                filtered_chunk = chunk[chunk[name_col].str.contains(keyword, case=False, na=False)]
                
                for _, row in filtered_chunk.iterrows():
                    products_list.append({
                        "name": str(row[name_col]).strip(),
                        "price_current": str(row[price_col]).strip(),
                        "image": str(row[image_col]).strip(),
                        "link": str(row[link_col]).strip()
                    })
                    
                # KIỂM TRA: Nếu kho đã gom đủ 30,000 sản phẩm thì chủ động ngắt tiến trình
                if len(products_list) >= 30000:
                    break
            if len(products_list) >= 30000:
                break
                    
        print(f"✅ Đã gom đủ hàng cho siêu thị lớn! Tổng cộng: {len(products_list)} sản phẩm.")
        
        # Cắt chính xác lấy 30,000 sản phẩm đầu tiên
        final_products = products_list[:30000]
        
        # Ghi đè vào file JSON ở thư mục gốc để Web hốt xài
        current_dir = os.path.dirname(os.path.abspath(__file__))
        output_file = os.path.join(current_dir, "shopee_products.json")
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(final_products, f, ensure_ascii=False, indent=4)
            
        print(f"🎉 Đã cập nhật file shopee_products.json thành công!")
        file_size_mb = os.path.getsize(output_file) / (1024 * 1024)
        print(f"📂 Kích thước file JSON hiện tại: {file_size_mb:.2f} MB (Dung lượng lý tưởng cho 30k sản phẩm).")
        
    except Exception as e:
        print(f"❌ Lỗi xử lý: {str(e)}")
        raise e

if __name__ == "__main__":
    filter_shopee_datafeed()
