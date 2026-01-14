from PIL import Image
import io

MAX_IMAGE_SIZE = 1000000  # 1 MB


def strip_exif(img: Image.Image) -> Image.Image:
    """
    Strips EXIF metadata from an image by creating a new image with only pixel data.

    Args:
        img: PIL Image object.

    Returns:
        Image.Image: New image without metadata.
    """
    # Create a new image with the same mode and size, copying only pixel data
    data = list(img.getdata())
    img_stripped = Image.new(img.mode, img.size)
    img_stripped.putdata(data)
    return img_stripped


def resize_image(image_path, max_size=(3840, 2160), quality=85):
    """
    Resize an image, maintaining its aspect ratio, only if it exceeds max_size.
    Also strips EXIF metadata for privacy as recommended by Bluesky.

    Args:
        image_path (str): Path to the image.
        max_size (tuple): Maximum width and height of the resized image.
        quality (int): The quality level for saving the image, between 0 (worst) and 100 (best).

    Returns:
        tuple: (bytes of the processed image, dict with width and height)
    """
    with Image.open(image_path) as img:
        original_format = img.format

        if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
            img.thumbnail(max_size, Image.LANCZOS)

        # Get final dimensions after potential resize
        final_width, final_height = img.size

        # Strip EXIF metadata
        img_stripped = strip_exif(img)

        img_byte_arr = io.BytesIO()

        # Handle PNG separately to preserve transparency
        if original_format == 'PNG':
            img_stripped.save(img_byte_arr, format='PNG')
        else:
            img_stripped.save(img_byte_arr, format='JPEG', quality=quality)

        return img_byte_arr.getvalue(), {"width": final_width, "height": final_height}
