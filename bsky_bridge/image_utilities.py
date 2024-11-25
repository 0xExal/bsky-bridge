from PIL import Image
import io

MAX_IMAGE_SIZE = 1000000  # 1 MB

def resize_image(image_path, max_size=(3840, 2160), quality=85):
    """
    Resize an image, maintaining its aspect ratio, only if it exceeds max_size.

    Args:
        image_path (str): Path to the image.
        max_size (tuple): Maximum width and height of the resized image.
        quality (int): The quality level for saving the image, between 0 (worst) and 100 (best).

    Returns:
        bytes: Bytes of the resized image.
    """
    with Image.open(image_path) as img:
        format = img.format
        if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
            img.thumbnail(max_size, Image.LANCZOS)
        
        img_byte_arr = io.BytesIO()
        
        # Handle PNG separately to preserve transparency
        if format == 'PNG':
            img.save(img_byte_arr, format='PNG')
        else:
            img.save(img_byte_arr, format='JPEG', quality=quality)
        
        return img_byte_arr.getvalue()
