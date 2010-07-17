from webob import Response, exc

def root_view(request):
    return Response("This is the root")
