import types
import traceback
import copy
import json

def apply_transformation(data, code):
    try:
        # Debug: Print the incoming data type and code
        print(f"Data type: {type(data)}")
        print(f"Data content: {json.dumps(data, indent=2)}")
        print(f"Generated code:\n{code}")
        
        # Create a new module to safely execute code
        mod = types.ModuleType("transform_module")
        
        # Add necessary imports to the module
        mod.__dict__['copy'] = copy
        mod.__dict__['json'] = json
        
        # Execute the transformation code
        exec(code, mod.__dict__)

        if hasattr(mod, 'transform'):
            # Make a deep copy of data to prevent modifications to original
            data_copy = copy.deepcopy(data)
            result = mod.transform(data_copy)
            print(f"Transform result type: {type(result)}")
            return result
        else:
            return {"error": "No 'transform' function found in generated code."}

    except Exception as e:
        print(f"Exception in transformation: {str(e)}")
        print(f"Exception type: {type(e)}")
        return {"error": str(e), "traceback": traceback.format_exc()}