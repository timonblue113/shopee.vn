import pandas as pd
import json
import requests

def filter_shopee_datafeed():
    # Link Datafeed lớn của Accesstrade
    DATAFEED_URL = "http://datafeed.accesstrade.me/shopee.vn.csv"
    
    # DANH SÁCH TỪ KHÓA BẠN MUỐN BÁN (Thay đổi/thêm bớt tùy ý bạn)
    KEYWORDS = ["bàn phím cơ", "chuột máy tính", "tai nghe gaming", "lót chuột"]
    
    print("🚀 Đang kết nối và tải lướt Datafeed từ Accesstrade...")
    products_list = []
    
    try:
        # Tải file theo cụm 50,000 dòng để không bị tràn bộ nhớ máy ảo GitHub
        chunk_size = 50000
        
        # Datafeed của AT thường phân cách bằng dấu phẩy, dùng mã hóa utf-8
        for chunk in pd.read_csv(DATAFEED_URL, sep=',', chunksize=chunk_size, on_bad_lines='skip'):
            
            # Kiểm tra tên các cột thực tế để tránh lỗi KeyEncoder
            columns = [str(col).lower() for col in chunk.columns]
            
            # Tìm chính xác các cột dựa trên cấu trúc chuẩn của AT Datafeed
            name_col = [c for c in chunk.columns if 'name' in c.lower() or 'title' in c.lower()][0]
            price_col = [c for c in chunk.columns if 'price' in c.lower() or 'discount' in c.lower()][0]
            image_col = [c for c in chunk.columns if 'image' in c.lower() or 'thumb' in c.lower()][0]
            link_col = [c for c in chunk.columns if 'aff_link' in c.lower() or 'link' in c.lower()][0]
            
            # Tiến hành lọc theo từ khóa
            for keyword in KEYWORDS:
                filtered_chunk = chunk[chunk[name_col].str.contains(keyword, case=False, na=False)]
                
                for _, row in filtered_chunk.iterrows():
                    products_list.append({
                        "name": str(row[name_col]).strip(),
                        "price_current": str(row[price_col]).strip(),
                        "image": str(row[image_col]).strip(),
                        "link": str(row[link_col]).strip()
                    })
                    
        print(f"✅ Lọc dữ liệu xong! Tìm thấy {len(products_list)} sản phẩm phù hợp.")
        
        # Lấy tối đa 500 sản phẩm để tối ưu tốc độ load trang GitHub Pages
        final_products = products_list[:500]
        
        # Xuất file JSON nằm ngay tại thư mục gốc để index.html đọc trực tiếp
        with open("shopee_products.json", "w", encoding="utf-8") as f:
            json.dump(final_products, f, ensure_ascii=False, indent=4)
        print("🎉 Đã cập nhật file shopee_products.json!")
        
    except Exception as e:
        print(f"❌ Lỗi xử lý dữ liệu: {e}")

if __name__ == "__main__":
    filter_shopee_datafeed()
