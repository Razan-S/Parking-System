# Installation Guide

## Quick Setup

### Standard Installation (CPU and GPU with automatic detection)
```bash
pip install -r requirements.txt
```

### CUDA-Specific Installation (for systems with NVIDIA GPUs)
If you need explicit CUDA support and encounter issues with the standard requirements:
```bash
pip install -r requirements-cuda.txt
```

## Cross-Platform Compatibility

The main `requirements.txt` uses standard PyTorch versions that will automatically detect and use GPU if available, while falling back to CPU on systems without CUDA.

### For Different Environments:

1. **Development machines with NVIDIA GPU**: Use standard `requirements.txt`
2. **Production servers with specific CUDA requirements**: Use `requirements-cuda.txt`
3. **CPU-only systems**: Use standard `requirements.txt` (will install CPU versions)
4. **Mac with Apple Silicon**: Use standard `requirements.txt` (will use MPS backend)

## Python Version Compatibility

This project requires Python 3.11. To ensure compatibility:

1. Create virtual environment with Python 3.11:
   ```bash
   python3.11 -m venv venv
   ```

2. Activate virtual environment:
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`

3. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```

## Troubleshooting

### Issue: "Could not find a version that satisfies the requirement torch==2.5.1+cu121"

**Solution**: This happens when trying to install CUDA-specific PyTorch versions from the default PyPI. Use one of these approaches:

1. **Recommended**: Use the standard `requirements.txt` (already fixed)
2. **Manual installation**:
   ```bash
   pip install torch==2.5.1+cu121 torchvision==0.20.1+cu121 torchaudio==2.5.1+cu121 --index-url https://download.pytorch.org/whl/cu121
   ```

### Issue: Different machines have different hardware capabilities

The standard `requirements.txt` will:
- Install CPU version on machines without CUDA
- Automatically use GPU if CUDA is available
- Work across Windows, Linux, and macOS

## Best Practices for Team Development

1. **Use the standard `requirements.txt`** for most development
2. **Pin exact versions** to ensure reproducibility
3. **Document Python version requirements** (3.11 in this case)
4. **Use virtual environments** to isolate dependencies
5. **Test on target deployment environment** before releasing
