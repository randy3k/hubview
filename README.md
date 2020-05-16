# A simple server to preview private github repo

```
PROJECTID=$(gcloud config get-value project)
```

```
docker build . -t gcr.io/$PROJECTID/hubview
```

Test locally
```
docker run --rm -p 8080:8080 gcr.io/$PROJECTID/hubview:latest
```

Push image to Google Registry
```
gcloud auth configure-docker
docker push gcr.io/$PROJECTID/hubview
```

Alternatively, ultilize Googld Builds to build image
```
gcloud builds submit --tag gcr.io/$PROJECTID/hubview
```

Deploy to Google Cloud Run
```
gcloud run deploy --image gcr.io/$PROJECTID/hubview --platform managed --max-instances 1
```
