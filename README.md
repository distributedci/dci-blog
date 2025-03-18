# dci-blog

## requirements

- python3

## create a venv

    rm -rf venv
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt

## run dev server

    make devserver-global

## Create a new blog post

Add new file in `./content` with this format `YYYY-MM-DD-title-separated-by-dashes.md`.

If you need to add images in your blog post, create a folder with the same name as the markdown file in the `./content/images` folder (i.e. `mkdir content/images/YYYY-MM-DD-title-separated-by-dashes`).

Use the image in your blog post like this:

![good name for accessibility]({static}/images/YYYY-MM-DD-title-separated-by-dashes/my-image.png)

/!\ use {static} to detect missing images at build time

## see other options

    make
