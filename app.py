from flask import Flask, request, jsonify
from google.cloud import speech, storage
import os, uuid

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "service_account.json"
app = Flask(__name__)

@app.route('/transcribir', methods=['POST'])
def transcribir_audio():
    data = request.get_json()
    audio_url = data.get('url')
    if not audio_url:
        return jsonify({"error": "No se recibió la URL del audio"}), 400

    local_path = descargar_audio(audio_url)
    if not local_path:
        return jsonify({"error": "No se pudo descargar el audio"}), 500

    texto = transcribir(local_path)
    os.remove(local_path)
    return jsonify({"transcripcion": texto})

def descargar_audio(url):
    try:
        from urllib.parse import unquote, urlparse
        parsed = urlparse(url)
        object_path = unquote(parsed.path.split('/o/')[1])
        bucket_name = url.split("/")[2].split(".")[0]

        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(object_path)

        filename = f"temp/{uuid.uuid4()}.3gp"
        os.makedirs("temp", exist_ok=True)
        blob.download_to_filename(filename)
        return filename
    except Exception as e:
        print(e)
        return None

def transcribir(audio_path):
    client = speech.SpeechClient()
    with open(audio_path, "rb") as audio_file:
        content = audio_file.read()

    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.AMR,
        sample_rate_hertz=8000,
        language_code="es-MX"
    )
    response = client.recognize(config=config, audio=audio)
    return " ".join([r.alternatives[0].transcript for r in response.results])

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
