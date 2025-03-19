import json
import re
import os

path = "data\deepseek-r1-32b-distill-qwen/base-deepseek-r1-32b-distill-qwen"
input_name = "predictions_part7_base-deepseek-r1-32b-distill-qwen_deepseek-r1-32b-distill-qwen_2025-03-11 10-39-30"
output_name = "unthink" + input_name

input_file = os.path.join(path, input_name + '.jsonl')
output_file = os.path.join(path, output_name + '.jsonl')
with open(input_file, "r", encoding="utf-8") as infile, open(output_file, "w", encoding="utf-8") as outfile:
    for line in infile:
        data = json.loads(line)
        for key, value in data.items():
            cleaned_value = re.sub(r"<think>.*?</think>\n*", "", value, flags=re.DOTALL)
            data[key] = cleaned_value.strip()
        json.dump(data, outfile, ensure_ascii=False)
        outfile.write("\n")

print("Hoàn tất! File đã được xử lý và lưu vào", output_file)
