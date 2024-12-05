from PyQt6.QtWidgets import QApplication, QMainWindow, QFileDialog
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.uic import loadUi
from PyQt6 import QtCore
from easyocr import Reader
import cv2


# Tạo từ điển các mã biển số của tỉnh/thành phố
province_dict = {
    "41": "Thành phố Hồ Chí Minh", "50": "Thành phố Hồ Chí Minh", "51": "Thành phố Hồ Chí Minh", "52": "Thành phố Hồ Chí Minh", "53": "Thành phố Hồ Chí Minh", "54": "Thành phố Hồ Chí Minh", "55": "Thành phố Hồ Chí Minh", "56": "Thành phố Hồ Chí Minh", "57": "Thành phố Hồ Chí Minh", "58": "Thành phố Hồ Chí Minh", "59": "Thành phố Hồ Chí Minh",
    "29": "Hà Nội", "30": "Hà Nội", "31": "Hà Nội", "32": "Hà Nội", "33": "Hà Nội", "40": "Hà Nội",
    "43": "Đà Nẵng", "61": "Bình Dương", "39": "Đồng Nai", "60": "Đồng Nai", "79": "Khánh Hòa",
    "15": "Hải Phòng", "16": "Hải Phòng", "62": "Long An", "92": "Quảng Nam", "72": "Bà Rịa - Vũng Tàu",
    "47": "Đắk Lắk", "65": "Cần Thơ", "86": "Bình Thuận", "49": "Lâm Đồng", "75": "Thừa Thiên Huế",
    "68": "Kiên Giang", "99": "Bắc Ninh", "14": "Quảng Ninh", "36": "Thanh Hóa", "37": "Nghệ An",
    "34": "Hải Dương", "81": "Gia Lai", "93": "Bình Phước", "89": "Hưng Yên", "77": "Bình Định",
    "63": "Tiền Giang", "17": "Thái Bình", "98": "Bắc Giang", "28": "Hòa Bình", "67": "An Giang",
    "88": "Vĩnh Phúc", "70": "Tây Ninh", "20": "Thái Nguyên", "24": "Lào Cai", "18": "Nam Định",
    "76": "Quảng Ngãi", "71": "Bến Tre", "48": "Đắk Nông", "69": "Cà Mau", "64": "Vĩnh Long",
    "35": "Ninh Bình", "19": "Phú Thọ", "85": "Ninh Thuận", "78": "Phú Yên", "90": "Hà Nam",
    "38": "Hà Tĩnh", "66": "Đồng Tháp", "83": "Sóc Trăng", "82": "Kon Tum", "73": "Quảng Bình",
    "74": "Quảng Trị", "84": "Trà Vinh", "95": "Hậu Giang", "26": "Sơn La", "94": "Bạc Liêu",
    "21": "Yên Bái", "22": "Tuyên Quang", "27": "Điện Biên", "25": "Lai Châu", "12": "Lạng Sơn",
    "23": "Hà Giang", "97": "Bắc Kạn", "11": "Cao Bằng"
}

class MainApp(QMainWindow):
    def __init__(self):
        super(MainApp, self).__init__()
        # Nạp giao diện từ tệp trangchu.ui
        loadUi("trangchu.ui", self)

        # Biến lưu ảnh hiện tại và ảnh gốc
        self.current_image = None
        self.original_image = None  # Lưu ảnh gốc chưa thay đổi

        # Thiết lập căn giữa cho lbl_anh
        self.lbl_anh.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.lbl_anh.setScaledContents(False)

        # Kết nối sự kiện cho các nút
        self.btn_anh.clicked.connect(self.open_and_process_image)
        self.btn_chon_tc.clicked.connect(self.select_and_process_roi)

    def open_and_process_image(self):
        # Hiển thị hộp thoại chọn tệp
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Chọn ảnh",
            "",
            "Image Files (*.png *.jpg *.jpeg *.bmp);;All Files (*)"
        )
        if file_path:  # Kiểm tra nếu người dùng chọn tệp
            self.original_image = cv2.imread(file_path)  # Lưu ảnh gốc
            self.current_image = self.original_image.copy()  # Sao chép ảnh gốc để xử lý

            # Chuyển đổi ảnh từ BGR sang RGB (OpenCV dùng BGR, còn Qt dùng RGB)
            rgb_image = cv2.cvtColor(self.current_image, cv2.COLOR_BGR2RGB)

            # Lấy kích thước từ `lbl_anh` và giữ nguyên tỷ lệ
            label_width = self.lbl_anh.width()
            label_height = self.lbl_anh.height()

            # Tạo QImage từ numpy array
            height, width, channel = rgb_image.shape
            bytes_per_line = channel * width
            qt_image = QImage(rgb_image.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)

            # Chuyển đổi QImage thành QPixmap
            pixmap = QPixmap.fromImage(qt_image)

            # Hiển thị hình ảnh trong QLabel, scaled giữ tỷ lệ, mở rộng theo kích thước QLabel
            self.lbl_anh.setPixmap(pixmap.scaled(
                label_width,
                label_height,
                QtCore.Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                QtCore.Qt.TransformationMode.SmoothTransformation
            ))

            # Tự động nhận diện biển số khi hiển thị ảnh
            self.process_image(self.current_image)

    # Cập nhật phương thức nhận diện biển số với tỉnh/thành phố
    def select_and_process_roi(self):
        if self.original_image is None:
            self.txt_bienso.setText("Vui lòng chọn ảnh trước.")
            return

        # Chọn vùng ROI từ ảnh gốc
        roi = cv2.selectROI("Chọn vùng ảnh", self.original_image, False, False)
        # Khi chọn xong vùng, cửa sổ chọn sẽ bị đóng
        cv2.destroyWindow("Chọn vùng ảnh")

        if roi == (0, 0, 0, 0):
            self.txt_bienso.setText("Bạn chưa chọn vùng nào.")
            return

        # Cắt vùng ROI từ ảnh gốc
        x, y, w, h = roi
        roi_image = self.original_image[int(y):int(y + h), int(x):int(x + w)]

        # Tiến hành nhận diện biển số xe trên vùng đã cắt
        reader = Reader(['en'])
        detection = reader.readtext(roi_image)

        # Kiểm tra và hiển thị kết quả nhận diện
        if len(detection) == 0:
            self.txt_bienso.setText("Không nhận diện được biển số xe")
            self.txt_tinh_tp.setText("Không nhận diện được tỉnh thành")
        else:
            # Nếu có nhiều hàng, xử lý và hiển thị theo định dạng yêu cầu
            if len(detection) == 1:
                license_plate_text = detection[0][1]  # Biển số chỉ có một hàng
                province_code = license_plate_text[:2]  # Lấy 2 chữ số đầu làm mã tỉnh/thành phố
                province_name = province_dict.get(province_code, "Không xác định")
                self.txt_bienso.setText(license_plate_text)
                self.txt_tinh_tp.setText(province_name)
            else:
                # Nếu có 2 dòng, hiển thị theo dạng: [hàng 1] [hàng 2]
                line1 = detection[0][1]
                line2 = detection[1][1] if len(detection) > 1 else ""
                license_plate_text = f"[{line1}] [{line2}]"
                province_code = line1[:2]  # Lấy 2 chữ số đầu của dòng 1 làm mã tỉnh/thành phố
                province_name = province_dict.get(province_code, "Không xác định")
                self.txt_bienso.setText(license_plate_text)
                self.txt_tinh_tp.setText(province_name)

    def process_image(self, img):
        try:
            # Chuyển ảnh sang grayscale
            grayscale = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(grayscale, (5, 5), 0)
            edged = cv2.Canny(blurred, 10, 200)

            # Tìm các đường viền
            contours, _ = cv2.findContours(edged, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            contours = sorted(contours, key=cv2.contourArea, reverse=True)[:5]

            # Xác định hình chữ nhật cho biển số xe
            number_plate_shape = None
            for c in contours:
                perimeter = cv2.arcLength(c, True)
                approximation = cv2.approxPolyDP(c, 0.02 * perimeter, True)
                if len(approximation) == 4:  # Hình chữ nhật
                    number_plate_shape = approximation
                    break

            if number_plate_shape is None:
                self.txt_bienso.setText("Không tìm thấy biển số xe")
                return

            # Cắt vùng biển số xe
            (x, y, w, h) = cv2.boundingRect(number_plate_shape)
            number_plate = grayscale[y:y + h, x:x + w]

            # Nhận diện biển số xe bằng EasyOCR
            reader = Reader(['en'])
            detection = reader.readtext(number_plate)

            if len(detection) == 0:
                self.txt_bienso.setText("Không nhận diện được biển số xe")
            else:
                # Nếu có nhiều hàng, xử lý và hiển thị theo định dạng yêu cầu
                if len(detection) == 1:
                    license_plate_text = detection[0][1]  # Biển số chỉ có một hàng
                    province_code = license_plate_text[:2]  # Lấy 2 chữ số đầu làm mã tỉnh/thành phố
                    province_name = province_dict.get(province_code, "Không xác định")
                    self.txt_bienso.setText(license_plate_text)
                    self.txt_tinh_tp.setText(province_name)
                else:
                    # Nếu có 2 dòng, hiển thị theo dạng: [hàng 1] [hàng 2]
                    line1 = detection[0][1]
                    line2 = detection[1][1] if len(detection) > 1 else ""
                    license_plate_text = f"[{line1}] [{line2}]"
                    province_code = line1[:2]  # Lấy 2 chữ số đầu của dòng 1 làm mã tỉnh/thành phố
                    province_name = province_dict.get(province_code, "Không xác định")
                    self.txt_bienso.setText(license_plate_text)
                    self.txt_tinh_tp.setText(province_name)

                # Vẽ hình chữ nhật xung quanh biển số và hiển thị ảnh
                cv2.drawContours(img, [number_plate_shape], -1, (255, 0, 0), 3)
                pixmap = self.convert_cv_to_pixmap(img)
                self.lbl_anh.setPixmap(pixmap.scaled(
                    self.lbl_anh.width(),
                    self.lbl_anh.height(),
                    QtCore.Qt.AspectRatioMode.KeepAspectRatio
                ))
        except Exception as e:
            self.txt_bienso.setText(f"Lỗi: {str(e)}")

    def convert_cv_to_pixmap(self, cv_img):
        """Chuyển đổi ảnh OpenCV sang QPixmap"""
        height, width, channel = cv_img.shape
        bytes_per_line = 3 * width
        q_img = QImage(cv_img.data, width, height, bytes_per_line, QImage.Format.Format_BGR888)
        return QPixmap.fromImage(q_img)

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    main_window = MainApp()
    main_window.show()
    sys.exit(app.exec())