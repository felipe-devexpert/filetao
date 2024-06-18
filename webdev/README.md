## FileTAO Backend

We have open sourced the backend for FileTAO for those who wish to build upon their validator.

Feel free to use, modify, or monetize this code without restriction.

### Install
```bash
# Install torch-cpu
pip install torch==2.3.0+cpu -f https://download.pytorch.org/whl/torch_stable.html

# Install FileTAO
git clone https://github.com/ifrit98/storage-subnet
cd storage-subnet
python -m pip install -e .

# Update FastAPI to the latest version
python -m pip install fastapi==0.110.2 # Ignore the warning, bittensor uses an older version, but compatible.
```

## Usage
You can use the reamde with a simple uvicorn server:
```bash
uvicorn main:app --port PORT --reload
```

## Extended usage
You may choose to host this backend with a service like heroku, or choose to self-host. All the tools and primitives are available, and provided "as-is".