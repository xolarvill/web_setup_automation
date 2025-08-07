import json
from typing import Dict, List, Tuple, Any, Set
from collections import defaultdict

class JSONStructureComparator:
    def __init__(self):
        self.path_map1 = {}  # 存储文件1中每个路径对应的行号
        self.path_map2 = {}  # 存储文件2中每个路径对应的行号
    
    def extract_structure_with_lines(self, data: Any, prefix: str = "", line_offset: int = 0) -> Dict[str, int]:
        """
        递归提取JSON结构的键路径，并记录对应的行号
        """
        paths = {}
        
        if isinstance(data, dict):
            for i, (key, value) in enumerate(data.items()):
                current_path = f"{prefix}.{key}" if prefix else key
                # 简化的行号计算（实际应用中可能需要更精确的解析）
                current_line = line_offset + i + 1
                paths[current_path] = current_line
                
                # 递归处理嵌套结构
                nested_paths = self.extract_structure_with_lines(
                    value, current_path, current_line
                )
                paths.update(nested_paths)
                
        elif isinstance(data, list):
            if data:  # 非空列表
                # 对于数组，我们分析第一个元素的结构
                array_path = f"{prefix}[*]"
                paths[array_path] = line_offset + 1
                
                if isinstance(data[0], (dict, list)):
                    nested_paths = self.extract_structure_with_lines(
                        data[0], array_path, line_offset + 1
                    )
                    paths.update(nested_paths)
        
        return paths
    
    def compare_json_files(self, file1_path: str, file2_path: str) -> Dict:
        """
        比较两个JSON文件的结构相似度
        """
        try:
            # 读取JSON文件
            with open(file1_path, 'r', encoding='utf-8') as f1:
                data1 = json.load(f1)
            
            with open(file2_path, 'r', encoding='utf-8') as f2:
                data2 = json.load(f2)
            
            # 提取结构路径
            self.path_map1 = self.extract_structure_with_lines(data1)
            self.path_map2 = self.extract_structure_with_lines(data2)
            
            return self._analyze_similarity()
            
        except FileNotFoundError as e:
            return {"error": f"文件未找到: {e}"}
        except json.JSONDecodeError as e:
            return {"error": f"JSON解析错误: {e}"}
        except Exception as e:
            return {"error": f"未知错误: {e}"}
    
    def compare_json_data(self, data1: Any, data2: Any) -> Dict:
        """
        直接比较两个JSON数据结构的相似度
        """
        self.path_map1 = self.extract_structure_with_lines(data1)
        self.path_map2 = self.extract_structure_with_lines(data2)
        
        return self._analyze_similarity()
    
    def _analyze_similarity(self) -> Dict:
        """
        分析两个结构的相似度
        """
        paths1 = set(self.path_map1.keys())
        paths2 = set(self.path_map2.keys())
        
        # 计算交集、差集
        common_paths = paths1.intersection(paths2)
        only_in_file1 = paths1 - paths2
        only_in_file2 = paths2 - paths1
        
        # 计算相似度百分比
        total_unique_paths = len(paths1.union(paths2))
        similarity_percentage = (len(common_paths) / total_unique_paths * 100) if total_unique_paths > 0 else 100
        
        # 生成相同区域报告
        common_ranges = self._find_common_ranges(common_paths)
        
        # 生成详细报告
        report = {
            "similarity_percentage": round(similarity_percentage, 2),
            "total_paths_file1": len(paths1),
            "total_paths_file2": len(paths2),
            "common_paths_count": len(common_paths),
            "common_ranges": common_ranges,
            "detailed_analysis": {
                "common_paths": sorted(list(common_paths)),
                "only_in_file1": sorted(list(only_in_file1)),
                "only_in_file2": sorted(list(only_in_file2))
            },
            "summary": self._generate_summary(similarity_percentage, common_paths, only_in_file1, only_in_file2)
        }
        
        return report
    
    def _find_common_ranges(self, common_paths: Set[str]) -> List[Dict]:
        """
        找出相同路径对应的行号范围
        """
        if not common_paths:
            return []
        
        # 获取相同路径在两个文件中的行号
        common_lines = []
        for path in common_paths:
            line1 = self.path_map1.get(path, 0)
            line2 = self.path_map2.get(path, 0)
            common_lines.append({
                "path": path,
                "file1_line": line1,
                "file2_line": line2
            })
        
        # 按文件1的行号排序
        common_lines.sort(key=lambda x: x["file1_line"])
        
        # 找出连续的行号范围
        ranges = []
        if common_lines:
            current_range = {
                "file1_start": common_lines[0]["file1_line"],
                "file1_end": common_lines[0]["file1_line"],
                "file2_start": common_lines[0]["file2_line"],
                "file2_end": common_lines[0]["file2_line"],
                "paths": [common_lines[0]["path"]]
            }
            
            for item in common_lines[1:]:
                # 如果行号连续，扩展当前范围
                if (item["file1_line"] <= current_range["file1_end"] + 2):
                    current_range["file1_end"] = max(current_range["file1_end"], item["file1_line"])
                    current_range["file2_end"] = max(current_range["file2_end"], item["file2_line"])
                    current_range["paths"].append(item["path"])
                else:
                    # 否则，保存当前范围并开始新范围
                    ranges.append(current_range)
                    current_range = {
                        "file1_start": item["file1_line"],
                        "file1_end": item["file1_line"],
                        "file2_start": item["file2_line"],
                        "file2_end": item["file2_line"],
                        "paths": [item["path"]]
                    }
            
            ranges.append(current_range)
        
        return ranges
    
    def _generate_summary(self, similarity: float, common: Set, only1: Set, only2: Set) -> str:
        """
        生成摘要报告
        """
        if similarity >= 90:
            level = "极高"
        elif similarity >= 75:
            level = "高"
        elif similarity >= 50:
            level = "中等"
        elif similarity >= 25:
            level = "低"
        else:
            level = "极低"
        
        summary = f"结构相似度: {level} ({similarity}%)\n"
        summary += f"共同键路径: {len(common)} 个\n"
        
        if only1:
            summary += f"仅在文件1中存在: {len(only1)} 个键路径\n"
        if only2:
            summary += f"仅在文件2中存在: {len(only2)} 个键路径"
        
        return summary

def print_comparison_report(report: Dict):
    """
    打印格式化的比较报告
    """
    if "error" in report:
        print(f"错误: {report['error']}")
        return
    
    print("=" * 60)
    print("JSON结构相似度分析报告")
    print("=" * 60)
    
    print(f"\n📊 相似度: {report['similarity_percentage']}%")
    print(f"📁 文件1键路径数量: {report['total_paths_file1']}")
    print(f"📁 文件2键路径数量: {report['total_paths_file2']}")
    print(f"🤝 共同键路径数量: {report['common_paths_count']}")
    
    print(f"\n📋 摘要:")
    print(report['summary'])
    
    # 打印相同区域
    if report['common_ranges']:
        print(f"\n🎯 相同结构区域:")
        for i, range_info in enumerate(report['common_ranges'], 1):
            print(f"  区域 {i}:")
            print(f"    文件1: 第{range_info['file1_start']}-{range_info['file1_end']}行")
            print(f"    文件2: 第{range_info['file2_start']}-{range_info['file2_end']}行")
            print(f"    包含 {len(range_info['paths'])} 个键路径")
    
    # 打印详细差异
    details = report['detailed_analysis']
    if details['only_in_file1']:
        print(f"\n❌ 仅在文件1中存在的键路径 ({len(details['only_in_file1'])} 个):")
        for path in details['only_in_file1'][:5]:  # 只显示前5个
            print(f"    - {path}")
        if len(details['only_in_file1']) > 5:
            print(f"    ... 还有 {len(details['only_in_file1']) - 5} 个")
    
    if details['only_in_file2']:
        print(f"\n❌ 仅在文件2中存在的键路径 ({len(details['only_in_file2'])} 个):")
        for path in details['only_in_file2'][:5]:  # 只显示前5个
            print(f"    - {path}")
        if len(details['only_in_file2']) > 5:
            print(f"    ... 还有 {len(details['only_in_file2']) - 5} 个")

# 使用示例
if __name__ == "__main__":
    # 创建比较器实例
    comparator = JSONStructureComparator()
    
    # 示例1: 比较文件
    # report = comparator.compare_json_files("file1.json", "file2.json")
    # print_comparison_report(report)
    
    # 示例2: 直接比较JSON数据
    sample_data1 = {
        "user": {
            "id": 1,
            "name": "张三",
            "profile": {
                "age": 25,
                "email": "test@example.com"
            },
            "hobbies": ["reading", "coding"]
        },
        "settings": {
            "theme": "dark",
            "language": "zh-CN"
        }
    }
    
    sample_data2 = {
        "user": {
            "id": 2,
            "name": "李四",
            "profile": {
                "age": 30,
                "city": "北京"  # 新增字段
            },
            "hobbies": ["music", "sports"]
        },
        "config": {  # 不同的键名
            "theme": "light"
        }
    }
    
    print("示例比较:")
    #report = comparator.compare_json_data(sample_data1, sample_data2)
    report = comparator.compare_json_files('json_templates/mockup_tool.json','json_templates/mockup_universal_topic.json')
    print_comparison_report(report)