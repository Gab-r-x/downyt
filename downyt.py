import os
import re
from tqdm import tqdm
from pytubefix import Playlist, YouTube
from tenacity import stop_after_attempt, wait_fixed, retry

# Retorna o nome do arquivo limpo de caracteres especiais:
def clean_filename(filename):
    return re.sub(r'[<>:"/\\|?*]', '-', filename)

def download_playlist(playlist_url, resolution):
    playlist = Playlist(playlist_url)
    playlist_name = clean_filename(re.sub(r'\W+', '-', playlist.title))
    
    # Cria diretório para playlist se ele não existir:
    if not os.path.exists(playlist_name):
        os.mkdir(playlist_name)

    for index, video in enumerate(tqdm(playlist.videos, desc="Baixando a playlist", unit="video"), start=1):
        yt = YouTube(video.watch_url, on_progress_callback=progress_function)
        video_streams = yt.streams.filter(res=resolution)

        video_filename = clean_filename(f"{index}. {yt.title}.mp4")
        video_path = os.path.join(playlist_name, video_filename)

        # Verifica se o vídeo já foi baixado:
        if os.path.exists(video_path):
            print(f"{video_filename} já existe!")
            continue

        if not video_streams:
            highest_resolution_stream = yt.streams.get_highest_resolution()
            video_name = clean_filename(highest_resolution_stream.default_filename)
            print(f"Baixando {video_name} em {highest_resolution_stream.resolution}")
            download_with_retries(highest_resolution_stream, video_path)
        else:
            video_stream = video_streams.first()
            video_name = clean_filename(video_stream.default_filename)
            print(f"Baixando video: {video_name} em {resolution}")
            download_with_retries(video_stream, "video.mp4")

            audio_stream = yt.streams.get_audio_only()
            print(f"Baixando audio: {video_name}")
            download_with_retries(audio_stream, "audio.mp4")

            # Junta os arquivos de audio e vídeo:
            os.system(
                "ffmpeg -y -i video.mp4 -i audio.mp4 -c:v copy -c:a aac final.mp4 -loglevel quiet -stats")
            os.rename("final.mp4", video_path)
            os.remove("video.mp4")
            os.remove("audio.mp4")

        print("_______________________________________________")


@retry(stop=stop_after_attempt(5), wait=wait_fixed(2))
def download_with_retries(stream, filename):
    stream.download(filename=filename)


def progress_function(stream, chunk, bytes_remaining):
    total_size = stream.filesize
    bytes_downloaded = total_size - bytes_remaining
    percentage_of_completion = bytes_downloaded / total_size * 100
    print(f"Baixando... {percentage_of_completion:.2f}% completados", end="\r")

if __name__ == "__main__":
    playlist_url = input("Enter the playlist url: ")
    resolutions = ["240p", "360p", "480p", "720p", "1080p", "1440p", "2160p"]
    resolution = input(f"Please select a resolution {resolutions}: ")
    download_playlist(playlist_url, resolution)