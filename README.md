# dci-blog

## requirements

- python3
- podman

## build and run blog

    podman build -t dci-blog .
    podman run -p 8080:8080 localhost/dci-blog

## develop

### create a venv

    rm -rf venv
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt

### run dev server

    make devserver-global

### see other option

    make
