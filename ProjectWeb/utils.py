def format_money(value):
    """Filter dùng trong HTML: {{ 100000 | format_money }}"""
    if value is None: return "0₫"
    return "{:,.0f}₫".format(value)

def clean_input_money(money_str):
    """Chuyển input form thành số nguyên"""
    if not money_str: return 0
    if isinstance(money_str, (int, float)): return int(money_str)
    clean_str = str(money_str).replace(",", "").replace(".", "").replace("₫", "").replace("VND", "").strip()
    return int(clean_str) if clean_str.isdigit() else 0