

from webob import Response, exc

from mediagoblin.edit import forms
from mediagoblin.decorators import require_active_login, get_media_entry_by_id


def may_edit_media(request, media):
    """Check, if the request's user may edit the media details"""
    if media['uploader'] == request.user['_id']:
        return True
    if request.user['is_admin']:
        return True
    return False
    

@get_media_entry_by_id
@require_active_login
def edit_media(request, media):
    if not may_edit_media(request, media):
        return exc.HTTPForbidden()

    form = forms.EditForm(request.POST,
        title = media['title'],
        slug = media['slug'],
        description = media['description'])

    if request.method == 'POST' and form.validate():
        media['title'] = request.POST['title']
        media['description'] = request.POST['description']
        media['slug'] = request.POST['slug']
        media.save()

        # redirect
        return exc.HTTPFound(
            location=request.urlgen("mediagoblin.user_pages.media_home",
                user=media.uploader()['username'], media=media['_id']))

    # render
    template = request.template_env.get_template(
        'mediagoblin/edit/edit.html')
    return Response(
        template.render(
            {'request': request,
             'media': media,
             'form': form}))
