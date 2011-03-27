import datetime

from webob import Response, exc
import wtforms

from mediagoblin import models

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

        entry = request.db.MediaEntry()
        entry['title'] = request.POST['title']
        entry['description'] = request.POST.get(['description'])o
        entry['media_type'] = u'image'

        # TODO this does NOT look save, we should clean the filename somenow?
        entry['file_store'] = request.POST['file'].filename

        entry.save(validate=True)

        # save file to disk
        ## TODO
        #open('/tmp/read_file.png', 'wb').write(request.POST['file'].file.read())


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
