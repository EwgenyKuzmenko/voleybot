from django import template

register = template.Library()

@register.filter
def get_qrcode_path(item):
    QRCodePath = f"voleybotapp/qrcodes/{item.QRCodeValue}.png"
    return QRCodePath