# A simple server to preview private github repo

```
PROJECTID=$(gcloud config get-value project)
```

```
docker build . -t gcr.io/$PROJECTID/repoview
```

Test locally
```
docker run --rm -p 8080:8080 gcr.io/$PROJECTID/repoview:latest
```

Push image to Google Registry
```
gcloud auth configure-docker
docker push gcr.io/$PROJECTID/repoview
```

Alternatively, ultilize Googld Builds to build image
```
gcloud builds submit --tag gcr.io/$PROJECTID/repoview
```

Deploy to Google Cloud Run
```
gcloud run deploy --image gcr.io/$PROJECTID/repoview --platform managed --max-instances 1
```
