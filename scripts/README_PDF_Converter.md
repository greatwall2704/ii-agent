# HTML Slides to PDF Converter

Bộ công cụ chuyển đổi các file slide HTML thành PDF với khả năng render chính xác, hỗ trợ JavaScript và các thành phần động.

## Tính năng

### 🎯 Render Chính Xác
- Sử dụng headless browser để render HTML/CSS/JavaScript
- Hỗ trợ biểu đồ động (Chart.js, D3.js, etc.)
- Bảo toàn layout, màu sắc, font chữ như trên trình duyệt

### 🚀 Nhiều Engine Render
- **Playwright** (khuyến nghị): Hiệu năng tốt nhất, hỗ trợ JS tối ưu
- **Selenium**: Tương thích cao, ổn định
- **wkhtmltopdf**: Nhanh, nhẹ, hỗ trợ JS cơ bản

### 📄 Tùy Chỉnh PDF
- Nhiều kích thước trang (A4, Letter, etc.)
- Hướng ngang/dọc
- Tùy chỉnh margin, scale
- Tối ưu hóa cho slide presentation

### 🔄 Tự Động Phát Hiện
- Tự động phát hiện thứ tự slide từ `presentation.html`
- Fallback sang thứ tự alphabet
- Xử lý đặc biệt cho single-page slides

## Cài Đặt

### 1. Cài đặt dependencies
```bash
# Tự động cài đặt tất cả dependencies
./scripts/convert_slides.sh --install

# Hoặc cài đặt thủ công
pip install -r scripts/requirements_pdf.txt

# Nếu dùng Playwright (khuyến nghị)
python -m playwright install chromium

# Nếu dùng wkhtmltopdf
sudo apt-get install wkhtmltopdf  # Ubuntu/Debian
# hoặc
brew install wkhtmltopdf          # macOS
```

## Sử Dụng

### Script Wrapper (Dễ nhất)
```bash
# Chuyển đổi cơ bản
./scripts/convert_slides.sh -s ./path/to/slides -o presentation.pdf

# Sử dụng engine khác
./scripts/convert_slides.sh -s ./slides -e selenium -o output.pdf

# Tùy chỉnh format
./scripts/convert_slides.sh -s ./slides -f A4 -r portrait
```

### Sử dụng trực tiếp Python

#### Playwright (Khuyến nghị)
```bash
python scripts/html_slides_to_pdf_playwright.py \
    --src-dir ./slides \
    --out presentation.pdf \
    --page-format A4 \
    --orientation landscape \
    --scale 1.0
```

#### Selenium
```bash
python scripts/html_slides_to_pdf.py \
    --src-dir ./slides \
    --out presentation.pdf \
    --page-size A4 \
    --orientation landscape
```

#### wkhtmltopdf
```bash
python scripts/html_slides_to_pptx.py \
    --src-dir ./slides \
    --out presentation.pdf
```

## Cấu Trúc Thư Mục Slides

### Cấu trúc được hỗ trợ:
```
slides/
├── presentation.html          # File chính (tùy chọn)
├── slide1.html               # Slide riêng lẻ
├── slide2.html
├── slide3.html
├── styles/                   # CSS files
├── images/                   # Hình ảnh
└── js/                      # JavaScript files
```

### Thứ tự slide:
1. **Từ presentation.html**: Tự động phát hiện từ:
   ```javascript
   const slides = ['slide1.html', 'slide2.html', 'slide3.html'];
   // hoặc
   loadSlide('slide1.html');
   loadSlide('slide2.html');
   ```

2. **Thứ tự alphabet**: Nếu không có presentation.html

3. **Single page**: Nếu chỉ có index.html

## Tùy Chọn Nâng Cao

### Playwright Options
```bash
python scripts/html_slides_to_pdf_playwright.py \
    --src-dir ./slides \
    --out presentation.pdf \
    --page-format A4 \
    --orientation landscape \
    --wait-timeout 30000 \
    --load-delay 2.0 \
    --scale 1.0
```

### Selenium Options  
```bash
python scripts/html_slides_to_pdf.py \
    --src-dir ./slides \
    --out presentation.pdf \
    --page-size A4 \
    --orientation landscape \
    --wait-timeout 10 \
    --load-delay 2.0
```

## Tối Ưu Hóa Slides cho PDF

### CSS cho Print Media
```css
@media print {
    /* Đảm bảo màu sắc được in */
    * {
        -webkit-print-color-adjust: exact !important;
        print-color-adjust: exact !important;
    }
    
    /* Ẩn các element không cần thiết */
    .no-print, .navigation, .controls {
        display: none !important;
    }
    
    /* Đảm bảo slide fill trang */
    .slide {
        width: 100% !important;
        height: 100vh !important;
        page-break-after: always !important;
    }
}
```

### JavaScript Optimization
```javascript
// Đảm bảo chart được render trước khi PDF tạo
function ensureChartsReady() {
    return new Promise((resolve) => {
        if (typeof Chart !== 'undefined') {
            // Wait for Chart.js
            setTimeout(resolve, 1000);
        } else {
            resolve();
        }
    });
}

// Signal ready state
window.slideReady = true;
```

## Troubleshooting

### Vấn đề thường gặp:

1. **JavaScript không chạy**
   - Tăng `--load-delay`
   - Kiểm tra console errors
   - Sử dụng Playwright thay vì wkhtmltopdf

2. **Màu sắc bị mất**
   - Thêm CSS print styles
   - Đảm bảo `print-background: true`

3. **Layout bị vỡ**
   - Kiểm tra responsive CSS
   - Tùy chỉnh `--scale` parameter
   - Sử dụng fixed dimensions

4. **File quá lớn**
   - Tối ưu hóa hình ảnh
   - Giảm DPI nếu có thể
   - Nén PDF sau khi tạo

### Debug Mode
```bash
# Enable logging
export PYTHONPATH=$PYTHONPATH:.
python -u scripts/html_slides_to_pdf_playwright.py --src-dir ./slides --out test.pdf
```

## So Sánh Engine

| Engine | Tốc độ | Chất lượng | JS Support | Cài đặt |
|--------|-------|-----------|-----------|---------|
| Playwright | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Dễ |
| Selenium | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Trung bình |
| wkhtmltopdf | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | Khó |

## Examples

### Chuyển đổi slides với biểu đồ Chart.js
```bash
./scripts/convert_slides.sh -s ./chart-slides -e playwright -o charts.pdf
```

### Batch conversion nhiều thư mục
```bash
for dir in slide-*; do
    ./scripts/convert_slides.sh -s "$dir" -o "${dir}.pdf"
done
```

### Custom styling cho specific presentation
```bash
python scripts/html_slides_to_pdf_playwright.py \
    --src-dir ./company-presentation \
    --out company-slides.pdf \
    --page-format Letter \
    --orientation landscape \
    --scale 0.8 \
    --load-delay 3.0
```

## License

Xem file LICENSE trong repository.

## Contributing

1. Fork repository
2. Tạo feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request
