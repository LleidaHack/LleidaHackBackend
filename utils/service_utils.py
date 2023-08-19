def set_existing_data(db_obj, req_obj):
    data = req_obj.dict(exclude_unset=True)
    for key, value in data.items():
        setattr(db_obj, key, value)
    return list(data.keys())