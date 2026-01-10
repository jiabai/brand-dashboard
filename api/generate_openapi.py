import json
import os
import sys

# 添加项目根目录到 sys.path，以便能导入 api 模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def generate_openapi():
    from api.main import app

    openapi_data = app.openapi()
    
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'openapi.json')
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(openapi_data, f, ensure_ascii=False, indent=2)
    
    print(f"OpenAPI documentation generated at: {output_path}")

if __name__ == "__main__":
    generate_openapi()
