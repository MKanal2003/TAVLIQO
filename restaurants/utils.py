import qrcode
from pathlib import Path
from django.conf import settings


def generate_qr_code(restaurant, request):
    """
    Generate a QR code for a restaurant's menu, saved to media/qr_codes/<slug>.png.
    Uses the token-based URL (opaque, non-guessable).
    """
    menu_url = request.build_absolute_uri(restaurant.get_menu_url())

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=12,
        border=4,
    )
    qr.add_data(menu_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="#0B1D42", back_color="#F4F6FA")

    qr_dir = Path(settings.MEDIA_ROOT) / 'qr_codes'
    qr_dir.mkdir(parents=True, exist_ok=True)

    qr_path = qr_dir / f'{restaurant.slug}.png'
    img.save(str(qr_path))

    return f'qr_codes/{restaurant.slug}.png'