from insightface.app import FaceAnalysis

app = FaceAnalysis(name="buffalo_l")
app.prepare(ctx_id=0)

print(app.models.keys())

recognition_model = app.models["recognition"]

print(type(recognition_model))
print(dir(recognition_model))