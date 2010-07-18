import datetime

from webob import Response, exc
import wtforms

def root_view(request):
    return Response("This is the root")


class ImageSubmitForm(wtforms.Form):
    title = wtforms.TextField(
        'Title',
        [wtforms.validators.Length(min=1, max=500)])
    description = wtforms.TextAreaField('Description of this work')
    file = wtforms.FileField('File')


def submit_test(request):
    image_form = ImageSubmitForm(request.POST)
    if request.method == 'POST' and image_form.validate():
        # create entry and save in database
        work_id = request.app.db.works.insert(
            {'title': image_form.title.data,
             'created': datetime.datetime.now(),
             'description': image_form.description.data})

        # save file to disk
        ## TODO

        # resize if necessary
        ## Hm.  This should be done on a separate view?

        # redirect
        pass

    # render
    template = request.template_env.get_template(
        'mediagoblin/test_submit.html')
    return Response(
        template.render(
            {'request': request,
             'image_form': image_form}))
