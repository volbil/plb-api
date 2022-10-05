from webargs import fields, validate

offset_args = {
    "offset": fields.Int(missing=0, validate=validate.Range(min=0))
}

token_list_args = {
    "offset": fields.Int(missing=0, validate=validate.Range(min=0)),
    "count": fields.Int(missing=50, validate=validate.Range(min=0)),
    "search": fields.Str(missing="")
}

range_args = {
    "offset": fields.Int(missing=30, validate=validate.Range(min=0))
}

unspent_args = {
    "amount": fields.Int(missing=0, validate=validate.Range(min=0)),
    "token": fields.Str(missing="PLB")
}

broadcast_args = {
    "raw": fields.Str(required=True)
}

verify_args = {
    "address": fields.Str(required=True),
    "signature": fields.Str(required=True),
    "message": fields.Str(required=True)
}
