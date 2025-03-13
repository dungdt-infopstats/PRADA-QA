import subprocess

# Danh sách các bộ 3 biến
type_list = ['base', 'base_code', 'base_description', 'base_description_code', 'qa']

model_list = [
    'qwen2.5:14b-instruct',
    'qwen2.5-coder:14b-instruct-fp16',
    'qwen2.5:7b-instruct',
    'qwen2.5-coder:7b-instruct',
    'mistral:7b-instruct',
]

part_list = ['9']
# Lặp qua từng bộ 3 biến và chạy main.py
for type_ in type_list:
    for model in model_list:
        for part in part_list:
            subprocess.run(["python", "main.py", model, type_, part])