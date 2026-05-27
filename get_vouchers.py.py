import os
import json
import requests

def get_shopee_vouchers_official_v2():
    # Endpoint chuẩn theo tài liệu tìm kiếm danh sách thông tin khuyến mãi
    API_URL = "https://api.accesstrade.vn/v1/offers_informations"
    API_KEY = "5ZYbgIAp67OIsN4VXQS0lQkCNvbU2zj-"
    
    headers = {
        "Authorization": f"Token {API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Tham số cấu hình chuẩn theo tài liệu
    params = {
        "merchant": "shopee",  # Lọc đích danh sàn Shopee theo tài liệu
        "limit": 100,          # Lấy tối đa 100 voucher ngon nhất
        "page": 1
    }
    
    print("🚀 Đang kết nối API v1/offers_informations để hốt Voucher Shopee...")
    
    try:
        response = requests.get(API_URL, headers=headers, params=params, timeout=15)
        
        if response.status_code == 200:
            result = response.json()
            voucher_list = []
            
            # Cấu trúc trả về là một mảng nằm trong key "data"
            if "data" in result and isinstance(result["data"], list):
                for item in result["data"]:
                    
                    # 1. Lấy tiêu đề voucher (Tài liệu dùng trường 'name')
                    v_title = item.get("name") or item.get("banner_title") or "Mã Giảm Giá Shopee"
                    
                    # 2. Lấy nội dung mô tả (Tài liệu dùng trường 'content')
                    v_desc = item.get("content") or "Bấm vào để xem chi tiết ưu đãi trên Shopee"
                    
                    # 3. Lấy link phân phối (Tài liệu dùng trường 'aff_link')
                    v_link = item.get("aff_link") or "https://shopee.vn"
                    
                    # 4. Trích xuất mã coupon từ mảng 'coupons' nếu có
                    v_coupon_code = ""
                    if item.get("coupons") and isinstance(item["coupons"], list) and len(item["coupons"]) > 0:
                        v_coupon_code = item["coupons"][0].get("coupon_code", "")
                    
                    # Đóng gói dữ liệu sạch
                    voucher_list.append({
                        "title": str(v_title).strip(),
                        "code": str(v_coupon_code).strip() if v_coupon_code else "HOT DEAL",
                        "desc": str(v_desc).strip()[:60] + "..." if len(str(v_desc)) > 60 else str(v_desc).strip(),
                        "link": v_link
                    })
            
            print(f"🎯 Kết quả: Đã cào thành công {len(voucher_list)} Voucher Shopee thực tế từ API.")
            
            # Khởi động chế độ mồi bất tử nếu API hôm đó trống trơn
            if len(voucher_list) == 0:
                print("⚠️ API trống hoặc chưa cập nhật mã trực tuyến, kích hoạt dữ liệu mồi...")
                voucher_list = [
                    {"title": "Miễn Phí Vận Chuyển 0Đ", "code": "FREESHIP", "desc": "Áp dụng toàn sàn cho mọi đơn hàng Shopee hôm nay", "link": "https://shopee.vn"},
                    {"title": "Giảm Ngay 50K Toàn Sàn", "code": "SĂN DEAL", "desc": "Đơn tối thiểu từ 0Đ dành cho khách hàng may mắn", "link": "https://shopee.vn"},
                    {"title": "Hoàn Xu 15% Toàn Quốc", "code": "CASHBACK", "desc": "Tối đa 100k xu khi thanh toán qua ví ShopeePay", "link": "https://shopee.vn"}
                ]

            # Lưu trực tiếp vào thư mục chứa file code này để index.html đọc được liền
            current_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in locals() else os.getcwd()
            output_file = os.path.join(current_dir, "shopee_vouchers.json")
            
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(voucher_list, f, ensure_ascii=False, indent=4)
                
            print(f"🎉 Đã xuất file thành công tại: {output_file}")
            
        else:
            print(f"❌ API báo lỗi hệ thống (Status {response.status_code}): {response.text}")
            
    except Exception as e:
        print(f"❌ Gặp sự cố trong quá trình cào dữ liệu: {str(e)}")

if __name__ == "__main__":
    get_shopee_vouchers_official_v2()
