from pprint import pprint

def formatErrors(errors):    
    result = []
    if isinstance(errors, dict):
        for field in errors.keys():
            if errors[field][0] == 'User with this Email already exists.':
                errors[field][0] = 'email-exists'
            result.append({"loc": ["form", field], "msg": errors[field][0], "type": "value_error.missing" })
        return result
    else:
        if hasattr(errors, "_message"):
            result.append({"loc": ["form", "email"], "msg": errors._message, "type": "" })
        else:
            for err in errors:
                result.append({"loc": err['loc'], "msg": err['msg'], "type": err['type'] })
        return result
    