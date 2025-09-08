# II Agent System Prompt Optimization với GEPA

Đây là một implementation để optimize system prompt của II Agent sử dụng framework GEPA với model Qwen3-Coder-A35B.

## Tổng quan

Script này sử dụng GEPA (Genetic-Pareto optimization) để tự động cải thiện system prompt của II Agent thông qua:
- Reflective mutation: Sử dụng LLM để phân tích lỗi và đề xuất cải tiến
- Evaluation trên các task đa dạng
- Pareto frontier management để tối ưu multiple objectives

## Cài đặt

1. Cài đặt dependencies:
```bash
pip install -r requirements.txt
```

2. System prompt gốc đã có sẵn tại: `ii_agent_system_prompt.txt`

## Sử dụng

### Cách 1: Chạy trực tiếp Python script
```bash
python optimize_ii_agent_prompt.py \
    --model_name "Qwen3-Coder-A35B" \
    --base_url "https://95819c637082.ngrok.app/v1" \
    --api_key "dummy" \
    --max_metric_calls 100 \
    --reflection_minibatch_size 2 \
    --run_dir "ii_agent_optimization_results"
```

### Cách 2: Sử dụng script có sẵn

**Trên Linux/Mac:**
```bash
chmod +x run_optimization.sh
./run_optimization.sh
```

**Trên Windows:**
```cmd
run_optimization.bat
```

## Tham số

- `--model_name`: Tên model để optimize (mặc định: "Qwen3-Coder-A35B")
- `--base_url`: URL endpoint của API (mặc định: "https://95819c637082.ngrok.app/v1")
- `--api_key`: API key (mặc định: "dummy")
- `--max_metric_calls`: Số lượng tối đa metric calls (mặc định: 100)
- `--reflection_minibatch_size`: Kích thước minibatch cho reflection (mặc định: 2)
- `--run_dir`: Thư mục lưu kết quả (mặc định: "ii_agent_optimization")

## Dataset

Script sử dụng dataset tự tạo với các task đa dạng để test II Agent:

### Training Tasks:
- Market analysis và reporting
- Web application development
- Data processing và insights
- Presentation creation
- Academic writing
- API deployment
- Dashboard creation
- Email automation

### Validation Tasks:
- Cloud provider comparison
- E-commerce development
- Sales trend analysis
- Chatbot development

## Kết quả

Sau khi chạy xong, bạn sẽ có:

1. **optimized_system_prompt.txt**: System prompt đã được optimize
2. **optimization_results.json**: Kết quả chi tiết bao gồm:
   - Best score đạt được
   - Lịch sử optimization
   - So sánh độ dài prompt
   - Metadata khác

## Kiến trúc

### IIAgentAdapter
- Tích hợp với GEPA framework
- Đánh giá performance trên multiple tasks
- Tạo reflective dataset cho improvement

### Evaluation Metrics
- Keyword matching với expected behavior
- Response length và quality indicators
- Tool usage (message_user)
- Planning indicators

### Reflective Dataset Creation
- Phân tích lỗi chi tiết
- Feedback specific cho II Agent capabilities
- Scoring dựa trên multiple criteria

## Customization

Bạn có thể customize:

1. **Dataset**: Thêm/sửa tasks trong `create_ii_agent_dataset()`
2. **Evaluation**: Sửa logic trong `_evaluate_response()`
3. **Feedback**: Customize feedback generation trong `make_reflective_dataset()`
4. **Model settings**: Thay đổi temperature, max_tokens, etc.

## Troubleshooting

1. **API Connection Issues**: Kiểm tra base_url và api_key
2. **Model Errors**: Đảm bảo model name chính xác
3. **Memory Issues**: Giảm minibatch_size hoặc max_metric_calls
4. **File Not Found**: Kiểm tra đường dẫn tới system prompt file

## Monitoring

Script sẽ in ra:
- Progress updates
- Current scores
- Best improvements
- Error messages (nếu có)

Để track chi tiết hơn, bạn có thể enable wandb bằng cách set `use_wandb=True` trong script.

## File Structure

```
ii_agent_optimize/
├── ii_agent_system_prompt.txt     # Original system prompt
├── optimize_ii_agent_prompt.py    # Main optimization script
├── requirements.txt               # Dependencies
├── run_optimization.sh           # Linux/Mac runner
├── run_optimization.bat          # Windows runner
├── README.md                     # This file
└── ii_agent_optimization_results/ # Output folder (created after running)
    ├── optimized_system_prompt.txt
    └── optimization_results.json
```
