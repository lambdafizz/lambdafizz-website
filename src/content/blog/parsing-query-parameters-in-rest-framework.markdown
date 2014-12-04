Title: Parsing query parameters in rest framework
Subtitle: and breaking from the limitations of your mind...
Author: Karol Majta
Date: 2013-05-18 08:49
Tags: Python, Django, REST

It has always bothered me that you have to parse query parameters manually
in django-rest-framework views, and there is no *generic* way to do it.

## The old way

Basically I used to do it like this:

    ::python
    class MyView(APIView):
        def get(request):
            count = request.QUERY_PARAMS.get('count', None)
            if count is None:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            try:
                count = int(count)
            except ValueError:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            
            # do your work

This is the most tedious, repetetive and error prone method of parsing query
params I can imagine, yet my code is liberally sprinkled with it. Why?

We'll basically, for some weird reason I kept thinking: *hmm... serializers?
they're good for POST.* After a brief talk with Tom Christie I kept scratching
my head and thinking why I did not figure this out myself!

## Serializers are good for any dict

And they are really well suited for parsing `request.QUERY_PARAMS` and they
save you **plenty** of lines.

The superb new way of doing this:

    ::python
    class MyQueryParamsExpectations(serializers.Serializer)
        count = fields.IntegerField()
    
    class MyView(APIView):
        def get(request):
            qpe = MyQueryParamsExpectations(data=request.QUERY_PARAMS)
            if not qpe.is_valid():
                return Response(
                    data=qpe.errors,
                    status=status.HTTP_400_BAD_REQUEST
                )
            qp = qpe.object
            
            # do your work and be happy with less code :)

This is actually uber-awesome, because you can easily reuse query params
serializers between multiple views.
