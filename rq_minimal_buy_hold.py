def init(context):
    context.stock = "000001.XSHE"
    context.fired = False


def handle_bar(context, bar_dict):
    if not context.fired:
        order_target_percent(context.stock, 0.5)
        context.fired = True
