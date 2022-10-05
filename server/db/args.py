from webargs import fields, validate

page_args = {
    "page": fields.Int(missing=1, validate=validate.Range(min=1)),
    "size": fields.Int(missing=10, validate=validate.Range(min=1, max=100))
}

page_args_richlist = {
    "page": fields.Int(missing=1, validate=validate.Range(min=1)),
    "size": fields.Int(missing=10, validate=validate.Range(min=1, max=100000))
}

broadcast_args = {
    "raw": fields.Str(required=True)
}

tokens_args = {
    "page": fields.Int(missing=1, validate=validate.Range(min=1)),
    "size": fields.Int(missing=10, validate=validate.Range(min=1, max=100)),
    "search": fields.Str(missing=None)
}

chart_args = {
    "resolution": fields.Str(missing="1D", validate=lambda r: r in ["1D", "1M", "1Y"]),
    "currency": fields.Str(missing="PLB")
}
