

from webob import Response, exc

from mediagoblin.edit import forms
from mediagoblin.edit.lib import may_edit_media
from mediagoblin.decorators import require_active_login, get_user_media_entry


@get_user_media_entry
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
        try:
            media.save()
        except Exception as e:
            return exc.HTTPConflict(detail = str(e))

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
