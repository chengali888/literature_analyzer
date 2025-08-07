import os
import json
import requests
import time
import base64
from tqdm import tqdm
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path
from config import Config

# 加载配置
config = Config()

# API配置
API_KEY = config.get('o3_api_key')
if not API_KEY:
    raise ValueError("O3 API密钥未配置，请运行 'python config.py setup' 进行配置")

# 初始化 OpenAI 客户端
client = OpenAI(
    api_key=API_KEY,
    base_url=config.get('o3_base_url', 'https://api.o3.fan/v1')
)
model = config.get('o3_model', 'claude-sonnet-4-20250514')

def call_o3(prompt, temperature=0.2, retries=3, images=None):
    """调用O3 API，支持图片输入"""
    for attempt in range(retries):
        try:
            messages = [
                {"role": "system", "content": "You are a precise extractor for ML literature and an expert chemist specializing in polyionic liquids and molecular structures."},
                {"role": "user", "content": prompt}
            ]
            
            # 如果有图片，添加到消息中
            if images:
                user_content = [{"type": "text", "text": prompt}]
                for img_base64 in images:
                    user_content.append({
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{img_base64}"
                        }
                    })
                messages[1]["content"] = user_content
            
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"[Retry {attempt+1}] API call failed: {e}")
            if attempt < retries - 1:
                time.sleep(5)  # 增加重试间隔
    
    return ""

def encode_image_to_base64(image_path):
    """将图片文件编码为base64"""
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        print(f"Error encoding image {image_path}: {e}")
        return None

def extract_abstract(content):
    """从markdown内容中提取摘要"""
    content_lower = content.lower()
    
    # 方法1: 查找包含"abstract"的部分
    abstract_keywords = ['abstract', 'Abstract', 'ABSTRACT']
    
    for keyword in abstract_keywords:
        if keyword.lower() in content_lower:
            # 找到abstract关键词的位置
            start_idx = content_lower.find(keyword.lower())
            if start_idx != -1:
                # 从abstract后面开始提取
                abstract_start = start_idx + len(keyword)
                
                # 查找下一个段落分隔符或关键词
                end_markers = ['\n\n', '\n#', '\n##', '\nintroduction', '\nkeywords', '\n1.', '\n1 ']
                end_idx = len(content)
                
                for marker in end_markers:
                    marker_idx = content_lower.find(marker.lower(), abstract_start)
                    if marker_idx != -1 and marker_idx < end_idx:
                        end_idx = marker_idx
                
                abstract = content[abstract_start:end_idx].strip()
                if len(abstract) > 50:  # 确保有足够内容
                    return abstract
    
    # 方法2: 如果没找到abstract关键词，使用前800个字符
    if len(content) > 50:
        return content[:800]
    
    return ""

def is_relevant_to_pils(abstract):
    """使用大模型API判断摘要是否与polyionic liquids (PILs) used in lithium-ion batteries相关"""
    if not abstract:
        return False
    
    prompt = f"""
You are an expert in materials science and battery technology. Please analyze the given abstract and determine if it is relevant to "polyionic liquids (PILs) used in lithium-ion batteries".

Abstract to analyze:
\"\"\"{abstract}\"\"\"

Criteria for relevance:
1. The research should involve polyionic liquids (PILs), polymeric ionic liquids, or ionic liquid polymers
2. The application should be related to lithium-ion batteries, energy storage, or electrochemical systems
3. Alternative terms include: polymer electrolytes with ionic liquid components, solid polymer electrolytes with ionic liquids, etc.

Please respond with ONLY one word: "RELEVANT" or "NOT_RELEVANT"

Your answer:"""
    
    try:
        response = call_o3(prompt, temperature=0.1, retries=2)
        response = response.strip().upper()
        
        if "RELEVANT" in response and "NOT_RELEVANT" not in response:
            return True
        elif "NOT_RELEVANT" in response:
            return False
        else:
            # 如果API响应不清晰，使用关键词作为备用方案
            print(f" Warning: Unclear API response for relevance: {response}, using keyword fallback")
            return _fallback_pils_relevance(abstract)
            
    except Exception as e:
        print(f" Error in API relevance check: {e}, using keyword fallback")
        return _fallback_pils_relevance(abstract)

def _fallback_pils_relevance(abstract):
    """备用的关键词匹配方法"""
    abstract_lower = abstract.lower()
    
    # PILs相关关键词
    pils_keywords = [
        'polyionic liquid', 'poly ionic liquid', 'polymeric ionic liquid', 
        'PIL', 'PILs', 'ionic liquid polymer', 'polymerized ionic liquid',
        'polymer electrolyte', 'solid polymer electrolyte'
    ]
    
    # 锂电池相关关键词
    battery_keywords = [
        'lithium', 'battery', 'electrolyte', 'ionic conductivity', 
        'electrochemical', 'energy storage', 'lithium ion', 'li-ion',
        'solid electrolyte', 'separator'
    ]
    
    # 检查是否包含PILs相关关键词
    has_pils = any(keyword in abstract_lower for keyword in pils_keywords)
    
    # 检查是否包含电池相关关键词
    has_battery = any(keyword in abstract_lower for keyword in battery_keywords)
    
    # 只有同时包含PILs和电池相关关键词才认为相关
    return has_pils or (has_battery and ('ionic liquid' in abstract_lower or 'polymer' in abstract_lower))

def is_review_article(abstract):
    """使用大模型API判断是否为综述文章"""
    if not abstract:
        return False
    
    prompt = f"""
You are an expert in academic literature classification. Please analyze the given abstract and determine if it describes a REVIEW article or a RESEARCH article.

Abstract to analyze:
\"\"\"{abstract}\"\"\"

Criteria for REVIEW articles:
1. Provides an overview, summary, or survey of existing research
2. Discusses multiple studies, methods, or materials from different sources
3. Uses terms like "review", "overview", "survey", "recent advances", "state of the art", "progress", "perspective"
4. Focuses on summarizing and analyzing existing knowledge rather than presenting new experimental results
5. Often discusses trends, challenges, and future directions in a research field

Criteria for RESEARCH articles:
1. Presents new experimental results, synthesis, or novel findings
2. Describes specific materials, methods, and experimental procedures
3. Reports original data, measurements, or characterizations
4. Focuses on "this work", "we synthesized", "we investigated", "our results"

Please respond with ONLY one word: "REVIEW" or "RESEARCH"

Your answer:"""
    
    try:
        response = call_o3(prompt, temperature=0.1, retries=2)
        response = response.strip().upper()
        
        if "REVIEW" in response and "RESEARCH" not in response:
            return True
        elif "RESEARCH" in response:
            return False
        else:
            # 如果API响应不清晰，使用关键词作为备用方案
            print(f" Warning: Unclear API response for article type: {response}, using keyword fallback")
            return _fallback_review_detection(abstract)
            
    except Exception as e:
        print(f" Error in API review detection: {e}, using keyword fallback")
        return _fallback_review_detection(abstract)

def _fallback_review_detection(abstract):
    """备用的关键词匹配方法"""
    abstract_lower = abstract.lower()
    
    # 综述文章的关键词
    review_keywords = [
        'review', 'overview', 'survey', 'perspective', 'progress',
        'recent advances', 'recent developments', 'state of the art',
        'comprehensive', 'critical review', 'mini review', 'brief review',
        'current status', 'recent progress', 'advances in', 'developments in'
    ]
    
    return any(keyword in abstract_lower for keyword in review_keywords)

def extract_text_info(content):
    """第一步：仅从文本提取信息，包含结构字段"""
    prompt = f"""
You are an expert assistant trained to extract structured data from materials science documents, especially on polyionic liquids (PILs) used in lithium-ion batteries.

Extract information from the text content only. If a field is not mentioned in the text, use "N/A" as the value.

Target format:
{{
  "meta": {{
  "name": "",
  "chemical formula": "",
  "molecular weight": {{"value": "", "unit": "g/mol"}},
  "structure type": "",
  "polymer backbone": "",
  "ionic liquid component": "",
  "molar_ratio": "",
  "concentration": {{
  "mol_per_L": {{"value": "", "unit": "mol/L"}},
  "mol_per_kg": {{"value": "", "unit": "mol/kg"}}
}}
  }},
  "molecular_structures": {{
    "polymer_backbone": {{
      "name": "",
      "smiles": "",
      "description": "",
      "molecular_weight": ""
    }},
    "ionic_liquid_cation": {{
      "name": "",
      "smiles": "",
      "description": "",
      "charge": "+1"
    }},
    "anion": {{
      "name": "",
      "smiles": "",
      "description": "",
      "charge": "-1"
    }},
    "monomer_unit": {{
      "name": "",
      "smiles": "",
      "description": ""
    }},
    "repeating_unit": {{
      "name": "",
      "smiles": "",
      "description": ""
    }},
    "crosslinker": {{
      "name": "",
      "smiles": "",
      "description": ""
    }}
  }},
  "structural_features": {{
    "alkyl_chain_length": "",
    "functional_groups": [],
    "degree_of_polymerization": "",
    "crosslinking_density": "",
    "molecular_architecture": ""
  }},
  "synthesis": {{
    "synthesis method": "",
    "precursors": [{{"name": "", "amount": "", "unit": ""}}],
    "polymerization conditions": {{
      "temperature": "",
      "time": "",
      "atmosphere": "",
      "catalyst": ""
    }},
    "purification method": "",
    "yield": ""
  }},
  "structure_characterization": {{
    "molecular structure": "",
    "degree_of_polymerization": "",
    "glass_transition_temperature": {{"value": "", "unit": ""}},
    "thermal_stability": {{"value": "", "unit": ""}},
    "morphology": "",
    "ion_association": {{
      "free_ion_ratio": {{"value": "", "unit": ""}},
      "contact_ion_pair_ratio": {{"value": "", "unit": ""}},
      "measurement_method": "",
      "temperature": ""
    }}
  }},
  "electrochemical_properties": {{
    "ionic_conductivity": {{
      "value": "",
      "unit": "",
      "temperature": "",
      "measurement_conditions": ""
    }},
    "lithium_transference_number": {{
      "value": "",
      "unit": "",
      "measurement_method": "",
      "temperature": ""
    }},
    "electrochemical_stability_window": {{"value": "", "unit": ""}},
    "interfacial_resistance": {{"value": "", "unit": ""}}
  }},
  "mechanical_properties": {{
    "bulk_modulus": {{
      "value": "",
      "unit": "",
      "measurement_method": "",
      "temperature": ""
    }},
    "tensile_strength": {{"value": "", "unit": ""}},
    "elongation_at_break": {{"value": "", "unit": ""}},
    "storage_modulus": {{"value": "", "unit": ""}}
  }},
  "battery_performance": {{
    "capacity": {{"value": "", "unit": ""}},
    "cycling_stability": "",
    "rate_capability": "",
    "coulombic_efficiency": {{"value": "", "unit": ""}}
  }},
  "crystal_structure": {{
    "crystal_system": "",
    "space_group": "",
    "lattice_parameters": "",
    "cif_available": false,
    "notes": ""
  }},
  "others": {{
    "applications": [],
    "advantages": [],
    "limitations": [],
    "dataset_source": "",
    "additional_information": ""
  }}
}}

Content:
\"\"\"{content}\"\"\"

Pay special attention to:
1. Chemical names and formulas for SMILES generation
2. Molecular structures and components
3. Any mention of crystallographic data
4. Structural features affecting properties

Only return the filled JSON. Do not include any explanations.
"""
    
    raw = call_o3(prompt)
    if "```json" in raw:
        raw = raw.split("```json")[1].split("```")[0].strip()
    elif "```" in raw:
        raw = raw.split("```")[1].strip()
    
    return raw

def extract_review_info(content):
    """针对综述文章的信息提取，提取多条结构-性质关系"""
    prompt = f"""
You are an expert assistant trained to extract structured data from REVIEW articles on polyionic liquids (PILs) used in lithium-ion batteries.

This is a REVIEW article, so extract ALL mentioned materials, structures, and their properties. Return an array of materials with the same JSON structure format.

Target format - Return an ARRAY of materials:
[
  {{
    "meta": {{
      "name": "",
      "chemical formula": "",
      "molecular weight": {{"value": "", "unit": "g/mol"}},
      "structure type": "",
      "polymer backbone": "",
      "ionic liquid component": "",
      "molar_ratio": "",
      "concentration": {{
        "mol_per_L": {{"value": "", "unit": "mol/L"}},
        "mol_per_kg": {{"value": "", "unit": "mol/kg"}}
      }}
    }},
    "molecular_structures": {{
      "polymer_backbone": {{
        "name": "",
        "smiles": "",
        "description": "",
        "molecular_weight": ""
      }},
      "ionic_liquid_cation": {{
        "name": "",
        "smiles": "",
        "description": "",
        "charge": "+1"
      }},
      "anion": {{
        "name": "",
        "smiles": "",
        "description": "",
        "charge": "-1"
      }},
      "monomer_unit": {{
        "name": "",
        "smiles": "",
        "description": ""
      }},
      "repeating_unit": {{
        "name": "",
        "smiles": "",
        "description": ""
      }},
      "crosslinker": {{
        "name": "",
        "smiles": "",
        "description": ""
      }}
    }},
    "structural_features": {{
      "alkyl_chain_length": "",
      "functional_groups": [],
      "degree_of_polymerization": "",
      "crosslinking_density": "",
      "molecular_architecture": ""
    }},
    "synthesis": {{
      "synthesis method": "",
      "precursors": [{{"name": "", "amount": "", "unit": ""}}],
      "polymerization conditions": {{
        "temperature": "",
        "time": "",
        "atmosphere": "",
        "catalyst": ""
      }},
      "purification method": "",
      "yield": ""
    }},
    "structure_characterization": {{
      "molecular structure": "",
      "degree_of_polymerization": "",
      "glass_transition_temperature": {{"value": "", "unit": ""}},
      "thermal_stability": {{"value": "", "unit": ""}},
      "morphology": "",
      "ion_association": {{
        "free_ion_ratio": {{"value": "", "unit": ""}},
        "contact_ion_pair_ratio": {{"value": "", "unit": ""}},
        "measurement_method": "",
        "temperature": ""
      }}
    }},
    "electrochemical_properties": {{
      "ionic_conductivity": {{
        "value": "",
        "unit": "",
        "temperature": "",
        "measurement_conditions": ""
      }},
      "lithium_transference_number": {{
        "value": "",
        "unit": "",
        "measurement_method": "",
        "temperature": ""
      }},
      "electrochemical_stability_window": {{"value": "", "unit": ""}},
      "interfacial_resistance": {{"value": "", "unit": ""}}
    }},
    "mechanical_properties": {{
      "bulk_modulus": {{
        "value": "",
        "unit": "",
        "measurement_method": "",
        "temperature": ""
      }},
      "tensile_strength": {{"value": "", "unit": ""}},
      "elongation_at_break": {{"value": "", "unit": ""}},
      "storage_modulus": {{"value": "", "unit": ""}}
    }},
    "battery_performance": {{
      "capacity": {{"value": "", "unit": ""}},
      "cycling_stability": "",
      "rate_capability": "",
      "coulombic_efficiency": {{"value": "", "unit": ""}}
    }},
    "crystal_structure": {{
      "crystal_system": "",
      "space_group": "",
      "lattice_parameters": "",
      "cif_available": false,
      "notes": ""
    }},
    "others": {{
      "applications": [],
      "advantages": [],
      "limitations": [],
      "dataset_source": "",
      "additional_information": "",
      "reference_info": ""
    }}
  }}
]

Content:
\"\"\"{content}\"\"\"

Special instructions for REVIEW articles:
1. Extract information for ALL mentioned PIL materials and their variants
2. Look for comparative data tables and performance summaries
3. Extract structure-property relationships mentioned in the text
4. Pay attention to different ionic liquid types, polymer backbones, and their combinations
5. Capture performance ranges and trends across different materials
6. Include information about advantages and limitations of each material type
7. Generate SMILES for as many structures as possible from chemical names or descriptions

Return the complete JSON array with all extracted materials. Include at least 3-5 different materials if mentioned in the review.
Only return the JSON array, no explanations.
"""
    
    raw = call_o3(prompt)
    if "```json" in raw:
        raw = raw.split("```json")[1].split("```")[0].strip()
    elif "```" in raw:
        raw = raw.split("```")[1].strip()
    
    return raw

def integrate_image_and_structure_data(text_json, image_paths, is_review=False):
    """第二步：分析图片并将信息整合到文本JSON中，重点关注结构信息"""
    if not image_paths:
        return text_json
    
    # 编码图片，限制数量以控制成本
    selected_images = image_paths[:10]  # 减少到10张图片以节省成本
    image_base64_list = []
    
    for img_path in selected_images:
        base64_data = encode_image_to_base64(img_path)
        if base64_data:
            image_base64_list.append(base64_data)
    
    if not image_base64_list:
        return text_json
    
    if is_review:
        # 对于综述文章，处理材料数组
        prompt = f"""
You are an expert at analyzing scientific figures and integrating molecular structure and property information from REVIEW articles.

I have extracted information from a REVIEW article text, and now I have additional figures/images. Please analyze the images and UPDATE/SUPPLEMENT the existing JSON array with information from the figures.

Current JSON array from text:
{json.dumps(text_json, indent=2)}

Instructions for REVIEW articles:
1. Analyze the provided scientific figures/charts/diagrams from the review
2. Extract comparative data, structure-property relationships, and performance summaries
3. **PRIORITY: Look for molecular structures, synthesis schemes, chemical formulas for generating SMILES**
4. UPDATE existing materials in the array by filling in "N/A" values where you find corresponding data
5. ADD new materials to the array if images show additional PIL structures not captured in text
6. Look for comparison tables, performance charts, and structural diagrams
7. Pay special attention to:
   - Chemical structure diagrams showing different PIL types
   - Comparative performance data (conductivity, mechanical properties, etc.)
   - Synthesis schemes and molecular architectures
   - Structure-property relationship summaries

For SMILES generation:
- Generate valid SMILES for as many structures as possible from diagrams
- Focus on different ionic liquid types, polymer backbones, and their combinations
- Include structural variations shown in figures

Return the UPDATED complete JSON array with the same format. Add new materials if found in images. Only return the JSON array, no explanations.
"""
    else:
        # 对于普通文章，处理单个材料对象
        prompt = f"""
You are an expert at analyzing scientific figures and integrating molecular structure and property information.

I have extracted some information from text, and now I have additional figures/images from the same scientific paper. Please analyze the images and UPDATE/SUPPLEMENT the existing JSON data with information from the figures.

Current JSON data from text:
{json.dumps(text_json, indent=2)}

Instructions:
1. Analyze the provided scientific figures/charts/diagrams
2. Extract numerical data, experimental conditions, and material properties
3. **PRIORITY: Look for molecular structures, synthesis schemes, chemical formulas, and structural diagrams to generate SMILES strings**
4. UPDATE the existing JSON by filling in "N/A" values where you find corresponding data in the images
5. ADD new information from images to appropriate fields
6. KEEP all existing non-"N/A" values unchanged unless the image provides more precise/complete information
7. If images contain structural data, update the "molecular_structures" section with valid SMILES
8. Look for crystallographic information if any crystal structures are shown
9. Pay special attention to:
   - Chemical structure diagrams
   - Synthesis schemes showing monomer and polymer structures
   - Molecular formulas and chemical names
   - Performance data (conductivity, mechanical properties, etc.)

For SMILES generation:
- Generate valid SMILES for polymer backbone, cation, anion, monomer, and repeating unit when possible
- If exact SMILES cannot be determined, provide chemical names or partial structures
- Note any structural features important for structure-property relationships

Return the UPDATED complete JSON structure with the same format. Only return the JSON, no explanations.
"""
    
    raw = call_o3(prompt, images=image_base64_list)
    
    if "```json" in raw:
        raw = raw.split("```json")[1].split("```")[0].strip()
    elif "```" in raw:
        raw = raw.split("```")[1].strip()
    
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        print(" Failed to parse integrated JSON, returning text-only version")
        return text_json

def process_folder(folder_path):
    """处理单个文件夹，增加预筛选和分类处理功能"""
    folder_name = os.path.basename(folder_path)
    # 使用简化的文件名避免路径过长问题
    simple_name = folder_name[:50] + "_" + str(hash(folder_name))[-8:]
    output_path = os.path.join(folder_path, f"{simple_name}_structure_property.json")
    
    # 检查是否已经处理过
    if os.path.exists(output_path):
        print(f" Already processed: {folder_name[:30]}...")
        return output_path
    
    # 查找md文件
    md_file = os.path.join(folder_path, "full.md")
    if not os.path.exists(md_file):
        print(f" No full.md found in: {folder_name[:30]}...")
        return None
    
    print(f"\n Processing: {folder_name[:30]}...")
    
    # 读取md文件内容
    try:
        with open(md_file, "r", encoding="utf-8") as f:
            md_content = f.read()
    except Exception as e:
        print(f" Error reading md file: {e}")
        return None
    
    # 🔍 预筛选步骤1：提取摘要
    print(" Step 0.1: Extracting abstract...")
    abstract = extract_abstract(md_content)
    if not abstract:
        print(" ❌ No abstract found, skipping...")
        return None
    
    print(f" Abstract extracted: {len(abstract)} characters")
    
    # 🔍 预筛选步骤2：检查是否与PILs相关（使用API）
    print(" Step 0.2: Checking relevance to polyionic liquids (using AI)...")
    if not is_relevant_to_pils(abstract):
        print(" ❌ Not relevant to polyionic liquids (PILs) used in lithium-ion batteries, skipping...")
        return None
    
    print(" ✅ Relevant to PILs for lithium-ion batteries")
    
    # 🔍 预筛选步骤3：判断文章类型（使用API）
    print(" Step 0.3: Determining article type (using AI)...")
    is_review = is_review_article(abstract)
    
    if is_review:
        print(" 📚 Detected as REVIEW article - will extract multiple materials")
        article_type = "review"
    else:
        print(" 📄 Detected as RESEARCH article - will extract single material")
        article_type = "research"
    
    # 🔍 第一步：根据文章类型提取信息
    print(f" Step 1: Extracting information from text ({article_type})...")
    try:
        if is_review:
            # 综述文章：提取多个材料
            text_extracted = extract_review_info(md_content)
            text_json = json.loads(text_extracted)
            # 确保是数组格式
            if not isinstance(text_json, list):
                text_json = [text_json] if text_json else []
            print(f" Extracted {len(text_json)} materials from review")
        else:
            # 研究文章：提取单个材料
            text_extracted = extract_text_info(md_content)
            text_json = json.loads(text_extracted)
            print(" Extracted single material data")
            
    except Exception as e:
        print(f" Error extracting text info: {e}")
        return None
    
    # 查找图片文件
    images_dir = os.path.join(folder_path, "images")
    image_paths = []
    if os.path.exists(images_dir):
        for img_file in os.listdir(images_dir):
            if img_file.lower().endswith(('.jpg', '.jpeg', '.png')):
                image_paths.append(os.path.join(images_dir, img_file))
    
    print(f" Found {len(image_paths)} images")
    
    # 🔍 第二步：整合图片信息和结构数据
    if image_paths and len(image_paths) <= 50:  # 处理更多图片的文件夹
        print(" Step 2: Analyzing images and integrating structure/property data...")
        try:
            final_json = integrate_image_and_structure_data(text_json, image_paths, is_review=is_review)
        except Exception as e:
            print(f" Error integrating image/structure data: {e}")
            final_json = text_json
    else:
        print(" Step 2: Skipping image integration (too many images or no images)")
        final_json = text_json
    
    # 添加处理元信息
    processing_info = {
        "processing_date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "num_images_analyzed": min(len(image_paths), 10) if image_paths else 0,
        "total_images": len(image_paths),
        "includes_structure_analysis": True,
        "original_folder_name": folder_name,
        "article_type": article_type,
        "is_review": is_review,
        "abstract_length": len(abstract),
        "pils_relevant": True
    }
    
    if is_review:
        # 综述文章：为每个材料添加元信息
        for i, material in enumerate(final_json):
            if isinstance(material, dict):
                material["processing_info"] = processing_info.copy()
                material["processing_info"]["material_index"] = i
                
                # 检查每个材料的结构数据完整性
                structures = material.get("molecular_structures", {})
                smiles_count = sum(1 for struct in structures.values() 
                                  if isinstance(struct, dict) and struct.get("smiles") and 
                                  struct.get("smiles") not in ["N/A", "", None])
                
                material["structure_completeness"] = {
                    "total_structure_fields": len(structures),
                    "filled_smiles_count": smiles_count,
                    "has_polymer_backbone": bool(structures.get("polymer_backbone", {}).get("smiles")),
                    "has_cation": bool(structures.get("ionic_liquid_cation", {}).get("smiles")),
                    "has_anion": bool(structures.get("anion", {}).get("smiles")),
                    "ready_for_ml": smiles_count >= 2  # 至少有2个有效SMILES
                }
        
        # 计算总的SMILES数量
        total_smiles = sum(material.get("structure_completeness", {}).get("filled_smiles_count", 0) 
                          for material in final_json if isinstance(material, dict))
        print(f" Extracted {total_smiles} total SMILES structures from {len(final_json)} materials")
        
    else:
        # 研究文章：单个材料处理
        final_json["processing_info"] = processing_info
        
        # 检查结构数据完整性
        structures = final_json.get("molecular_structures", {})
        smiles_count = sum(1 for struct in structures.values() 
                          if isinstance(struct, dict) and struct.get("smiles") and 
                          struct.get("smiles") not in ["N/A", "", None])
        
        final_json["structure_completeness"] = {
            "total_structure_fields": len(structures),
            "filled_smiles_count": smiles_count,
            "has_polymer_backbone": bool(structures.get("polymer_backbone", {}).get("smiles")),
            "has_cation": bool(structures.get("ionic_liquid_cation", {}).get("smiles")),
            "has_anion": bool(structures.get("anion", {}).get("smiles")),
            "ready_for_ml": smiles_count >= 2  # 至少有2个有效SMILES
        }
        
        print(f" Extracted {smiles_count} SMILES structures")
    
    # 保存结果
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            if is_review:
                # 综述文章：保存材料数组
                json.dump(final_json, f, ensure_ascii=False, indent=2)
            else:
                # 研究文章：保存单个材料
                json.dump([final_json], f, ensure_ascii=False, indent=2)
        print(f" ✅ Successfully saved {article_type} data")
        return output_path
        
    except Exception as e:
        print(f" Error saving file: {e}")
        return None

def collect_and_merge_results(base_dir, output_file="complete_structure_property_database.json"):
    """收集所有处理结果并合并，包含新的预筛选统计"""
    all_data = []
    review_count = 0
    research_count = 0
    
    # 查找所有输出文件
    for folder_name in os.listdir(base_dir):
        folder_path = os.path.join(base_dir, folder_name)
        if os.path.isdir(folder_path):
            # 查找该文件夹中的任何*_structure_property.json文件
            for file in os.listdir(folder_path):
                if file.endswith("_structure_property.json"):
                    output_file_path = os.path.join(folder_path, file)
                    try:
                        with open(output_file_path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            if isinstance(data, list):
                                all_data.extend(data)
                                # 统计文章类型
                                for item in data:
                                    if isinstance(item, dict):
                                        article_type = item.get("processing_info", {}).get("article_type", "unknown")
                                        if article_type == "review":
                                            review_count += 1
                                        elif article_type == "research":
                                            research_count += 1
                            else:
                                all_data.append(data)
                                article_type = data.get("processing_info", {}).get("article_type", "unknown")
                                if article_type == "review":
                                    review_count += 1
                                elif article_type == "research":
                                    research_count += 1
                    except Exception as e:
                        print(f"Error reading {output_file_path}: {e}")
                    break  # 只处理第一个找到的文件
    
    # 统计结构数据完整性
    total_records = len(all_data)
    ml_ready = sum(1 for d in all_data if d.get("structure_completeness", {}).get("ready_for_ml", False))
    has_structures = sum(1 for d in all_data if d.get("structure_completeness", {}).get("filled_smiles_count", 0) > 0)
    
    # 统计总SMILES数量
    total_smiles = sum(d.get("structure_completeness", {}).get("filled_smiles_count", 0) for d in all_data)
    
    # 创建数据库统计
    database_stats = {
        "database_info": {
            "creation_date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_records": total_records,
            "article_type_breakdown": {
                "review_articles": review_count,
                "research_articles": research_count
            },
            "records_with_smiles": has_structures,
            "total_smiles_extracted": total_smiles,
            "ml_ready_records": ml_ready,
            "structure_completeness_ratio": ml_ready/total_records if total_records > 0 else 0,
            "purpose": "Filtered structure-property relationship database for polyionic liquid inverse design",
            "filtering_criteria": [
                "Abstracts must contain polyionic liquid (PIL) keywords",
                "Must be relevant to lithium-ion battery applications",
                "Review articles extract multiple materials",
                "Research articles extract single materials"
            ]
        },
        "data": all_data
    }
    
    # 保存合并结果
    merged_path = os.path.join(base_dir, output_file)
    with open(merged_path, "w", encoding="utf-8") as f:
        json.dump(database_stats, f, ensure_ascii=False, indent=2)
    
    print(f"\n🎯 Filtered Structure-Property Database Created:")
    print(f"📁 File: {output_file}")
    print(f"📊 Total records: {total_records}")
    print(f"📚 Review articles: {review_count} (multiple materials per article)")
    print(f"📄 Research articles: {research_count} (single material per article)")
    print(f"🧬 Records with SMILES: {has_structures}")
    print(f"🔬 Total SMILES extracted: {total_smiles}")
    print(f"🤖 ML-ready records: {ml_ready}")
    print(f"✅ Completeness: {ml_ready/total_records*100:.1f}%" if total_records > 0 else "0%")
    
    return merged_path

def main():
    """主函数"""
    base_dir = "/home/zhilong-song/MinerU/results1"
    
    # 获取所有文件夹
    folders = []
    for item in os.listdir(base_dir):
        item_path = os.path.join(base_dir, item)
        if os.path.isdir(item_path):
            folders.append(item_path)
    
    print(f"🚀 Starting FILTERED structure-property extraction with pre-screening...")
    print(f"📂 Found {len(folders)} folders to process")
    print(f"🔍 Pre-screening criteria:")
    print(f"   ✅ Must contain abstract")
    print(f"   ✅ Must be relevant to polyionic liquids (PILs) in lithium-ion batteries")
    print(f"   📚 Review articles → extract multiple materials")
    print(f"   📄 Research articles → extract single material")
    print(f"="*60)
    
    # 处理每个文件夹
    processed_files = []
    failed_count = 0
    skipped_no_abstract = 0
    skipped_not_relevant = 0
    review_articles = 0
    research_articles = 0
    
    for i, folder_path in enumerate(folders, 1):
        print(f"\n[{i}/{len(folders)}]", end="")
        try:
            result = process_folder(folder_path)
            if result:
                processed_files.append(result)
                # 判断文章类型（简单检查文件内容）
                try:
                    with open(result, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if isinstance(data, list) and len(data) > 0:
                            article_type = data[0].get("processing_info", {}).get("article_type", "unknown")
                            if article_type == "review":
                                review_articles += 1
                            elif article_type == "research":
                                research_articles += 1
                except:
                    pass
            else:
                failed_count += 1
        except Exception as e:
            print(f" Unexpected error: {e}")
            failed_count += 1
        
        # 每处理20个文件夹休息一下，避免API限制
        if i % 20 == 0:
            print(f"\n ⏸️  Processed {i} folders, taking a break...")
            time.sleep(15)
    
    print(f"\n\n🎯 Pre-screening and Processing Results:")
    print(f"="*60)
    print(f"📂 Total folders examined: {len(folders)}")
    print(f"✅ Successfully processed: {len(processed_files)} folders")
    print(f"   📚 Review articles: {review_articles}")
    print(f"   📄 Research articles: {research_articles}")
    print(f"❌ Failed/Skipped: {failed_count} folders")
    print(f"   (Includes: no abstract, not PIL-relevant, processing errors)")
    
    # 合并结果
    if processed_files:
        merge_path = collect_and_merge_results(base_dir)
        print(f"\n🎉 Filtered PIL database ready for machine learning!")
        print(f"📊 Quality: Only PIL-relevant materials with structure data")
    else:
        print("\n❌ No successful extractions to merge.")
        print("💡 Consider expanding the relevance criteria or checking input data")

if __name__ == "__main__":
    main() 