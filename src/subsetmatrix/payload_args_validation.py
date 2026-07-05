def validate_args(*args) -> dict:
    """Validates args and delivers them organized in a preconceived dict."""
    res = {}
    all_args = [arg for arg in args]
    if not all_args:
        return res

    if isinstance(all_args[0], dict):
        points = all_args[0]
        y_temp = points.get("Y")
        x_temp = points.get("X")
        if isinstance(y_temp, dict) or isinstance(x_temp, dict):
            raise ValueError("Y and X should be lists or tuples, like so: 'Y': [1, 2, 3, 4, 5].")
        if isinstance(y_temp, list|tuple) and len(y_temp) > 2:
            # for now we keep iterables out of the story. Later on it makes sense to consider
            pairs = [p for p in y_temp if isinstance(p, list|tuple) and len(p) == 2]
            if len(pairs) > 2:
                res["Y"] = []
                res["X"] = []
                for i in pairs:
                    if isinstance(i[0], int|float|complex|str) and isinstance(i[1], int|float|complex|str):
                        res["X"].append(i[0])
                        res["Y"].append(i[1])
            else:
                res["Y"] = [x for x in y_temp if isinstance(x, int|float|complex|str)]
        elif isinstance(y_temp, dict) and len(y_temp) > 2:
            res["Y"] = []
            res["X"] = []
            for k, v in y_temp.items():
                if isinstance(k, int|float|complex|str) and isinstance(v, int|float|complex|str):
                    res["X"].append(k)
                    res["Y"].append(v)
        if isinstance(x_temp, list|tuple):
            res["X"] = [x for x in x_temp if isinstance(x, int|float|complex|str)]

    elif isinstance(all_args[0], list|tuple) and len(all_args[0]) > 2:
        y_temp = all_args[0]
        # I could seed directly into res["Y"] and res["X"], but checking if this fits sounds better
        pairs = [p for p in y_temp if isinstance(p, list|tuple) and len(p) == 2]
        if len(pairs) > 2:
            res["Y"] = []
            res["X"] = []
            for i in pairs:
                if isinstance(i[0], int|float|complex|str) and isinstance(i[1], int|float|complex|str):
                    res["X"].append(i[0])
                    res["Y"].append(i[1])
        elif not pairs:
            res["Y"] = [y for y in y_temp if isinstance(y, int|float|complex|str)]

    else:
        # by now we stablished args[0] wasn't a list|tuple, so it should
        # make no sense to treat args as pairs, therefore I'll just grab
        # whatever is args and not an iterable
        res["Y"] = [y for y in all_args if isinstance(y, int|float|complex|str)]
        res["residual_args"] = [r for r in all_args[1:] if not isinstance(r, int|float|complex|str)]
    
    if not res.get("Y"):
        return {"residual_args": all_args}

    if len(res["Y"]) < 3:
        raise ValueError("There should be more than two 'Y' entries.")
    if len(all_args) > 1 and not res.get("residual_args"):
        res["residual_args"] = all_args[1:]
    
    # I shouldn't worry about building X from list(range(len(res["Y"]))) now, only after calling both methods on object creation
    return res

def validate_kwargs(**kwargs) -> dict:
    """Validates kwargs and delivers them organized in a preconceived dict."""
    res = {}
    all_kwargs = dict(kwargs)
    if not all_kwargs:
        return res
    
    if "Y" in all_kwargs:
        y_temp = all_kwargs.get("Y") # it makes no sense to validate it to points since the
                                     # argument came as "Y" inside a kwarg, so I won't.
        
        if not isinstance(y_temp, list|tuple):
            raise ValueError("If you're trying to send Y values via kwarg, the value should be a list, like so: 'Y': [1, 2, 3, 4, 5].")

        if len(y_temp) > 2:
            res["Y"] = [y for y in y_temp if isinstance(y, int|float|complex|str)]
        
        res["residual_kwargs"] = {k:v for k, v in all_kwargs.items() if k != "Y" and k != "X"}

    if "X" in all_kwargs:
        x_temp = all_kwargs.get("X")
        if isinstance(x_temp, list|tuple) and len(x_temp) > 2:
            res["X"] = [x for x in x_temp if isinstance(x, int|float|complex|str)]
        if "residual_kwargs" not in res:
            res["residual_kwargs"] = {k: v for k, v in all_kwargs.items() if k != "Y" and k != "X"}

    if not "Y" in res and not "X" in res:
        if "points" in all_kwargs:
            points = all_kwargs.get("points")
            if not points:
                raise ValueError("Points should have values into it.")

            if "Y" in points:
                y_temp = points.get("Y")
                y_temp_temp = [y for y in y_temp if isinstance(y, int|float|complex|str)]
                if not y_temp_temp or len(y_temp_temp) < 3:
                    raise ValueError("There should be more than two 'Y' entries.")
                res["Y"] = y_temp_temp

            if "Y" in res and len(res["Y"]) > 2 and "X" in points:
                x_temp = points.get("X")
                x_temp_temp = [x for x in x_temp if isinstance(x, int|float|complex|str)]
                if not x_temp_temp or len(x_temp_temp) != len(res["Y"]):
                    raise ValueError("There should be the same amount of values in X than there are in Y.")
                res["X"] = x_temp_temp
            
            res["residual_kwargs"] = {k:v for k, v in all_kwargs.items() if k != "X" and k != "Y"}

    if not "points" in all_kwargs and not "Y" in all_kwargs:
        res["Y"] = []
        res["X"] = []
        for k, v in all_kwargs.items():
            if isinstance(k, int|float|complex|str) and isinstance(v, int|float|complex|str):
                res["X"].append(k)
                res["Y"].append(v)
        res["residual_kwargs"] = {k:v for k, v in all_kwargs.items() if not isinstance(k, int|float|complex|str) or not isinstance(v, int|float|complex|str)}

    if not "Y" in res:
        raise ValueError("No valid entry for Y values was detected in your keyword arguments.")

    if len(res["Y"]) < 3:
        raise ValueError("There should be more than two 'Y' entries.")

    if not "X" in res and "X" in all_kwargs:
        x_temp = all_kwargs.get("X")
        if not isinstance(x_temp, list|tuple):
            raise ValueError("X should be a list or a tuple.")
        x_temp_temp = [x for x in x_temp if isinstance(x, int|float|complex|str)]
        if len(x_temp_temp) != res["Y"]:
            raise ValueError("There should be an equal ammount of itens in X and Y.")

    return res
