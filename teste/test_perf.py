import time
import asyncio
from Backend.services.report_service import get_reports_data

def test():
    print("Testing get_reports_data...")
    start = time.time()
    try:
        # User ID 1 is usually Master
        data = get_reports_data(1, {'preview_nivel': 'Master'})
        print(f"Data loaded in {time.time() - start:.2f} seconds.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    test()
