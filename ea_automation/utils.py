def ensure_update_refresh(obj, collection=None):
    if hasattr(obj, 'Update'):
        obj.Update()
    
    if collection is not None:
        if hasattr(collection, 'Refresh'):
            collection.Refresh()