quantitative_variable_names = {
    "t1": "T1",
    "t2": "T2",
    "t2_map": "T2",
    "t2_map_20_echos": "T2",
    "t2_map_30_echos": "T2"
}


other_quantitative_variable_names = {
    "t1": ["Si", "delta"],
    "t2": ["Si"],
    "t2_map": [],
    "t2_map_20_echos": [],
    "t2_map_30_echos": []
}


def get_quantitative_variable(datatype):
    if datatype not in quantitative_variable_names:
        raise Exception(f"Unknown datatype: {datatype}")
    quant_col = quantitative_variable_names[datatype]
    return quant_col


def get_other_quantitative_variables(datatype):
    if datatype not in other_quantitative_variable_names:
        raise Exception(f"Unknown datatype: {datatype}")
    quant_cols = other_quantitative_variable_names[datatype]
    return quant_cols


def get_all_quantitative_variables(datatype):
    if datatype not in quantitative_variable_names:
        raise Exception(f"Unknown datatype: {datatype}")
    if datatype not in other_quantitative_variable_names:
        raise Exception(f"Unknown datatype: {datatype}")
    quant_cols = [quantitative_variable_names[datatype]]
    quant_cols.extend(other_quantitative_variable_names[datatype])
    return quant_cols
