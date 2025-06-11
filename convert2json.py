from typing import List
import json

def convert_to_json(segments: List[str]) -> str:
    """
    将分割后的文本段转换为JSON格式。
    """
    # skip 0 because it is the argument field 
    part1 = segments[1]
    part2 = segments[2]
    pass