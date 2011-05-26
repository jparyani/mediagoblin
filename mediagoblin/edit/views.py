

from webob import Response, exc

from mediagoblin.edit import forms
from mediagoblin.decorators import require_active_login, get_media_entry_by_id

@get_media_entry_by_id
@require_active_login
def edit_media(request, media):
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
