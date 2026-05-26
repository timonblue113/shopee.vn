import pandas as pd
import json
import os

def filter_shopee_datafeed():
    DATAFEED_URL = "http://datafeed.accesstrade.me/shopee.vn.csv"
    
    # RÚT NGẮN TỪ KHÓA ĐỂ ĐÓN ĐẦU DỮ LIỆU DỄ HƠN
    KEYWORDS = ["phím", "chuột", "tai nghe", "lót chuột", "gaming"]
    
    print("🚀 Đang kết nối và tải lướt Datafeed từ Accesstrade...")
    products_list = []
    backup_products = [] # Kho phòng hờ nếu bộ lọc bằng 0
    
    try:
        # Đọc thử 5 dòng đầu để map cột
        preview_df = pd.read_csv(DATAFEED_URL, sep=',', nrows=5, on_bad_lines='skip')
        
        name_col = 'name' if 'name' in preview_df.columns else preview_df.columns[1]
        price_col = 'discount' if 'discount' in preview_df.columns else ('price' if 'price' in preview_df.columns else preview_df.columns[3])
        image_col = 'image' if 'image' in preview_df.columns else preview_df.columns[5]
        link_col = 'url' if 'url' in preview_df.columns else preview_df.columns[2]

        print(f"🎯 Ánh xạ cột -> Name: {name_col} | Price: {price_col} | Link: {link_col}")

        # Bắt đầu đọc dữ liệu theo cụm
        chunk_size = 50000
        for chunk in pd.read_csv(DATAFEED_URL, sep=',', chunksize=chunk_size, on_bad_lines='skip'):
            
            # Chuyển toàn bộ cột tên về dạng chuỗi chuẩn để ép công thức tìm kiếm không bị lỗi font
            chunk[name_col] = chunk[name_col].astype(str)
            
            # Lưu lại một ít sản phẩm đầu tiên làm backup phòng hờ
            if len(backup_products) < 100:
                for _, row in chunk.head(100).iterrows():
                    backup_products.append({
                        "name": str(row[name_col]).strip(),
                        "price_current": str(row[price_col]).strip(),
                        "image": str(row[image_col]).strip(),
                        "link": str(row[link_col]).strip()
                    })

            # Tiến hành lọc theo từ khóa rút gọn
            for keyword in KEYWORDS:
                filtered_chunk = chunk[chunk[name_col].str.contains(keyword, case=False, na=False)]
                
                for _, row in filtered_chunk.iterrows():
                    products_list.append({
                        "name": str(row[name_col]).strip(),
                        "price_current": str(row[price_col]).strip(),
                        "image": str(row[image_col]).strip(),
                        "link": str(row[link_col]).strip()
                    })
                    
        # KIỂM TRA NẾU BỘ LỌC KHÔNG RA GÌ THÌ BỐC KHO BACKUP XÀI LUÔN
        if len(products_list) == 0:
            print("⚠️ Không tìm thấy sản phẩm theo từ khóa yêu cầu. Hệ thống tự động kích hoạt kho Deal ngẫu nhiên phòng hờ!")
            final_products = backup_products[:100]
        else:
            print(f"✅ Lọc dữ liệu thành công! Gom được: {len(products_list)} sản phẩm.")
            final_products = products_list[:500]
        
        # Ghi file JSON ra thư mục gốc
        current_dir = os.path.dirname(os.path.abspath(__file__))
        output_file = os.path.join(current_dir, "shopee_products.json")
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(final_products, f, ensure_ascii=False, indent=4)
            
        print(f"🎉 Đã ghi dữ liệu vào file thành công!")
        print(f"📂 Kích thước file hiện tại: {os.path.getsize(output_file)} bytes.")
        
    except Exception as e:
        print(f"❌ Lỗi: {str(e)}")
        raise e

if __name__ == "__main__":
    filter_shopee_datafeed()
