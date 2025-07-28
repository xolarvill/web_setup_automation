# test_numpy_import.py
import sys
import traceback

def test_numpy_import():
    print("Testing NumPy import in PyInstaller environment...")
    print(f"Python version: {sys.version}")
    print(f"Frozen: {getattr(sys, 'frozen', False)}")
    
    try:
        # 步骤1：导入基础numpy
        print("Step 1: Importing numpy...")
        import numpy as np
        print(f"✓ NumPy version: {np.__version__}")
        
        # 步骤2：测试numpy功能
        print("Step 2: Testing numpy functionality...")
        arr = np.array([1, 2, 3, 4, 5])
        print(f"✓ Created array: {arr}")
        print(f"✓ Array sum: {np.sum(arr)}")
        
        # 步骤3：导入pandas
        print("Step 3: Importing pandas...")
        import pandas as pd
        print(f"✓ Pandas version: {pd.__version__}")
        
        # 步骤4：测试pandas功能
        print("Step 4: Testing pandas functionality...")
        df = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})
        print("✓ Created DataFrame:")
        print(df)
        
        print("✅ All tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Full traceback:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_numpy_import()
    sys.exit(0 if success else 1)