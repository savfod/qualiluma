import os
import sys
import json
import requests
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path

def complex_data_processor(data_input, config_params, output_format="json", include_metadata=True, validate_input=False):
    processed_results = []
    error_count = 0
    warning_messages = []
    
    for item in data_input:
        try:
            if validate_input:
                if not isinstance(item, dict):
                    raise ValueError("Item must be dictionary")
                if "id" not in item:
                    raise KeyError("Missing required id field")
            
            processed_item = {}
            processed_item["original_id"] = item.get("id", "unknown")
            processed_item["timestamp"] = datetime.now().isoformat()
            
            if "value" in item:
                raw_value = item["value"]
                if isinstance(raw_value, str):
                    try:
                        processed_item["numeric_value"] = float(raw_value)
                    except ValueError:
                        processed_item["numeric_value"] = 0
                        warning_messages.append(f"Could not convert {raw_value} to float for item {item.get('id')}")
                elif isinstance(raw_value, (int, float)):
                    processed_item["numeric_value"] = float(raw_value)
                else:
                    processed_item["numeric_value"] = 0
                    warning_messages.append(f"Unexpected value type for item {item.get('id')}")
            
            if config_params.get("apply_transformations", False):
                transform_type = config_params.get("transform_type", "linear")
                if transform_type == "linear":
                    multiplier = config_params.get("linear_multiplier", 1.0)
                    offset = config_params.get("linear_offset", 0.0)
                    processed_item["transformed_value"] = processed_item["numeric_value"] * multiplier + offset
                elif transform_type == "logarithmic":
                    if processed_item["numeric_value"] > 0:
                        processed_item["transformed_value"] = np.log(processed_item["numeric_value"])
                    else:
                        processed_item["transformed_value"] = 0
                        warning_messages.append(f"Cannot apply log to non-positive value for item {item.get('id')}")
                elif transform_type == "exponential":
                    base = config_params.get("exp_base", 2.0)
                    processed_item["transformed_value"] = base ** processed_item["numeric_value"]
            
            if include_metadata:
                processed_item["metadata"] = {
                    "processing_time": datetime.now().isoformat(),
                    "config_used": config_params,
                    "warnings": len([w for w in warning_messages if str(item.get('id')) in w])
                }
            
            processed_results.append(processed_item)
            
        except Exception as e:
            error_count += 1
            error_item = {
                "original_id": item.get("id", "unknown"),
                "error": str(e),
                "error_type": type(e).__name__,
                "timestamp": datetime.now().isoformat()
            }
            if include_metadata:
                error_item["metadata"] = {"is_error": True}
            processed_results.append(error_item)
    
    final_result = {
        "processed_data": processed_results,
        "summary": {
            "total_items": len(data_input),
            "successful_items": len(processed_results) - error_count,
            "error_count": error_count,
            "warning_count": len(warning_messages),
            "processing_timestamp": datetime.now().isoformat()
        }
    }
    
    if warning_messages:
        final_result["warnings"] = warning_messages
    
    if output_format == "json":
        return json.dumps(final_result, indent=2)
    elif output_format == "dict":
        return final_result
    elif output_format == "csv":
        csv_lines = ["id,numeric_value,transformed_value,error"]
        for item in processed_results:
            csv_line = f"{item.get('original_id', '')},{item.get('numeric_value', '')},{item.get('transformed_value', '')},{item.get('error', '')}"
            csv_lines.append(csv_line)
        return "\n".join(csv_lines)
    else:
        return str(final_result)
