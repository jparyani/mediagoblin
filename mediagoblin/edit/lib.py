
def may_edit_media(request, media):
    """Check, if the request's user may edit the media details"""
    if media['uploader'] == request.user['_id']:
        return True
    if request.user['is_admin']:
        return True
    return False
