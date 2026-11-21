
import io
import qrcode

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage


def generate_qr_code(restaurant, request):
    """
    Generate a restaurant menu QR code and save it
    using Django's configured storage backend (Cloudinary).
    """

    menu_url = request.build_absolute_uri(
        restaurant.get_menu_url()
    )

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=12,
        border=4,
    )

    qr.add_data(menu_url)
    qr.make(fit=True)

    img = qr.make_image(
        fill_color="#0B1D42",
        back_color="#F4F6FA",
    )

    # Convert QR image into PNG bytes
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")

    file_name = f"qr_codes/{restaurant.slug}.png"

    # Remove the previous QR image if it exists
    if default_storage.exists(file_name):
        default_storage.delete(file_name)

    # Save using configured storage (Cloudinary)
    saved_name = default_storage.save(
        file_name,
        ContentFile(buffer.getvalue()),
    )

    # Return the complete image URL
    return default_storage.url(saved_name)
