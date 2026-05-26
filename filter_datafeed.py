import pandas as pd
import json
import os

def filter_shopee_datafeed():
    DATAFEED_URL = "http://datafeed.accesstrade.me/shopee.vn.csv"
    KEYWORDS = ["bàn phím cơ", "chuột máy tính", "tai nghe gaming", "lót chuột"]
    
    print("🚀 Đang kết nối và tải lướt Datafeed từ Accesstrade...")
    products_list = []
    
    try:
        # Đọc thử 5 dòng đầu tiên để ép in ra danh sách TÊN CỘT THỰC TẾ của Accesstrade
        preview_df = pd.read_csv(DATAFEED_URL, sep=',', nrows=5, on_bad_lines='skip')
        print("📋 DANH SÁCH CỘT THỰC TẾ TRÊN TÀI LIỆU AT:")
        print(list(preview_df.columns))
        
        # Thiết lập biến lưu tên cột chuẩn sau khi quét
        name_col, price_col, image_col, link_col = None, None, None, None
        
        # Thuật toán dò tìm thông minh hơn, không sợ lỗi IndexError [0] nữa
        for col in preview_df.columns:
            c_lower = str(col).lower()
            if 'name' in c_lower or 'title' in c_lower:
                name_col = col
            elif 'price' in c_lower or 'discount' in c_lower:
                price_col = col
            elif 'image' in c_lower or 'thumb' in c_lower:
                image_col = col
            elif 'link' in c_lower or 'url' in c_lower:
                link_col = col

        # Nếu thiếu bất kỳ cột cốt lõi nào, báo lỗi luôn để kiểm tra
        if not name_col or not link_col:
            print("❌ Không tìm thấy cấu trúc cột Name hoặc Link phù hợp trong file CSV!")
            return

        print(f"🎯 Đã ánh xạ cột thành công -> Name: {name_col} | Price: {price_col} | Link: {link_col}")

        # Bắt đầu đọc toàn bộ file theo chunk
        chunk_size = 50000
        for chunk in pd.read_csv(DATAFEED_URL, sep=',', chunksize=chunk_size, on_bad_lines='skip'):
            
            for keyword in KEYWORDS:
                # Tìm dòng chứa từ khóa
                filtered_chunk = chunk[chunk[name_col].str.contains(keyword, case=False, na=False)]
                
                for _, row in filtered_chunk.iterrows():
                    # Trích xuất dữ liệu an toàn kèm giá trị mặc định nếu rỗng
                    p_name = str(row[name_col]).strip() if name_col in chunk.columns else "N/A"
                    p_price = str(row[price_col]).strip() if price_col in chunk.columns else "0"
                    p_image = str(row[image_col]).strip() if image_col in chunk.columns else "N/A"
                    p_link = str(row[link_col]).strip() if link_col in chunk.columns else "N/A"
                    
                    products_list.append({
                        "name": p_name,
                        "price_current": p_price,
                        "image": p_image,
                        "link": p_link
                    })
                    
        print(f"✅ Lọc dữ liệu xong! Tổng cộng gom được: {len(products_list)} sản phẩm.")
        
        final_products = products_list[:500]
        
        # Chỉ định ghi đè trực tiếp vào thư mục làm việc hiện tại của Repository (Thư mục gốc)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        output_file = os.path.join(current_dir, "shopee_products.json")
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(final_products, f, ensure_ascii=False, indent=4)
            
        print(f"🎉 Đã xuất file JSON thành công tại vị trí: {output_file}")
        
        # Kiểm tra file thực sự tồn tại trước khi thoát
        if os.path.exists(output_file):
            print(f"📂 Xác nhận file dung lượng: {os.path.getsize(output_file)} bytes đang nằm ở thư mục gốc!")
        else:
            print("⚠️ Cảnh báo: Lệnh ghi chạy xong nhưng file không xuất hiện!")
            
    except Exception as e:
        print(f"❌ Toang ở bước xử lý dữ liệu: {str(e)}")
        # Ném lỗi ra ngoài để làm sập luôn bước 'Run filter script', giúp ta dễ đọc lỗi ở log chính
        raise e

if __name__ == "__main__":
    filter_shopee_datafeed()
