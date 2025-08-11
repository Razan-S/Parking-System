"""
Parking System Performance Testing Suite
Main launcher for data collection and validation applications.
"""

import sys
import os
import torch
# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def show_menu():
    print("=" * 50)
    print("   Parking System Performance Testing Suite")
    print("=" * 50)
    print()
    print("1. Data Collector - Capture frames and run AI detection")
    print("2. Validation App - Manual validation with GUI")
    print("3. Exit")
    print()

def run_data_collector():
    """Run the data collection script"""
    try:
        # Force CUDA initialization before importing data collector
        import torch
        if torch.cuda.is_available():
            # Initialize CUDA context to ensure GPU detection works
            test_tensor = torch.randn(1, 1).cuda()
            print(f"🚀 CUDA context initialized on {test_tensor.device}")
            del test_tensor
            torch.cuda.empty_cache()
        
        from data_collector import main as collector_main
        collector_main()
    except ImportError as e:
        print(f"Error importing data collector: {e}")
    except Exception as e:
        print(f"Error running data collector: {e}")

def run_validation_app():
    """Run the validation GUI application"""
    try:
        from validation_app import main as validation_main
        validation_main()
    except ImportError as e:
        print(f"Error importing validation app: {e}")
    except Exception as e:
        print(f"Error running validation app: {e}")

def main():
    while True:
        show_menu()
        choice = input("Enter your choice (1-3): ").strip()
        
        if choice == '1':
            print("\nStarting Data Collector...")
            run_data_collector()
        elif choice == '2':
            print("\nStarting Validation App...")
            run_validation_app()
        elif choice == '3':
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()
