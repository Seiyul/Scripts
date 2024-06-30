import json
import subprocess
import os

# Diccionario de códigos de idioma a nombres de idioma en español
language_map = {
    'en': 'Inglés',
    'es': 'Español',
    'fr': 'Francés',
    'de': 'Alemán',
    'zh': 'Chino',
    'ja': 'Japonés',
    'ru': 'Ruso',
    'it': 'Italiano',
    'pt': 'Portugués',
    'ar': 'Árabe',
    'ko': 'Coreano',
    'hi': 'Hindi',
    'bn': 'Bengalí',
    'pa': 'Panyabí',
    'jv': 'Javanés',
    'te': 'Telugú',
    'mr': 'Maratí',
    'tr': 'Turco',
    'ta': 'Tamil',
    'vi': 'Vietnamita',
    'ur': 'Urdu',
    'fa': 'Persa',
    'pl': 'Polaco',
    'uk': 'Ucraniano',
    'nl': 'Neerlandés',
    'ro': 'Rumano',
    'el': 'Griego',
    'hu': 'Húngaro',
    'cs': 'Checo',
    'sv': 'Sueco',
    'da': 'Danés',
    'fi': 'Finlandés',
    'no': 'Noruego',
    'he': 'Hebreo',
    'th': 'Tailandés',
    'id': 'Indonesio',
    'ms': 'Malayo',
    'my': 'Birmano',
    'km': 'Jemer',
    'am': 'Amárico',
    'bg': 'Búlgaro'
}

# Idiomas prioritarios
priority_languages = ['es', 'en', 'ja']

# Crear la carpeta "archivos" si no existe
if not os.path.exists('archivos'):
    os.makedirs('archivos')


def get_yt_dlp_formats(url):
    result = subprocess.run(['yt-dlp', '-F', url], capture_output=True, text=True)
    output = result.stdout
    columns = [
        {"COLUMN": "ID", "START": 0, "END": 6},
        {"COLUMN": "EXT", "START": 7, "END": 12},
        {"COLUMN": "RESOLUTION", "START": 13, "END": 23},
        {"COLUMN": "FPS", "START": 24, "END": 27},
        {"COLUMN": "CH", "START": 28, "END": 31},
        {"COLUMN": "FILESIZE", "START": 35, "END": 44},
        {"COLUMN": "TBR", "START": 45, "END": 49},
        {"COLUMN": "PROTO", "START": 50, "END": 55},
        {"COLUMN": "VCODEC", "START": 58, "END": 71},
        {"COLUMN": "VBR", "START": 72, "END": 77},
        {"COLUMN": "ACODEC", "START": 78, "END": 88},
        {"COLUMN": "ABR", "START": 89, "END": 93},
        {"COLUMN": "ASR", "START": 94, "END": 97},
        {"COLUMN": "MORE INFO", "START": 98, "END": -1}
    ]
    lines = output.strip().split('\n')[3:]
    formats = []
    for line in lines:
        if line.strip() == "" or line.startswith("─"):
            continue
        data = {}
        for col in columns:
            start = col["START"]
            end = col["END"] if col["END"] != -1 else None
            data[col["COLUMN"]] = line[start:end].strip() if end else line[start:].strip()
        formats.append(data)
    return formats


def get_video_title(url):
    result = subprocess.run(['yt-dlp', '--get-title', url], capture_output=True, text=True)
    return result.stdout.strip().replace(' ', '_')


def size_to_bytes(size):
    units = {"B": 1, "KiB": 1024, "MiB": 1024 ** 2, "GiB": 1024 ** 3, "TiB": 1024 ** 4}
    size = size.replace(" ", "")
    if size[-3:] in units:
        return float(size[:-3]) * units[size[-3:]]
    elif size[-2:] in units:
        return float(size[:-2]) * units[size[-2:]]
    else:
        return float(size)  # Assume bytes if no unit


def download_video_and_audio(url, formats, video_title):
    video_formats = [f for f in formats if f['FILESIZE'] and f['ACODEC'] == 'video only']

    if not video_formats:
        print("No se encontraron formatos de video adecuados.")
        return

    max_size_video = max(video_formats, key=lambda f: size_to_bytes(f['FILESIZE']))
    video_file = f"archivos/video-{video_title}.{max_size_video['EXT']}"
    print(f"Descargando el video con el mayor tamaño: ID {max_size_video['ID']} en {video_file}")
    subprocess.run(['yt-dlp', '-f', max_size_video['ID'], '-o', video_file, url])

    audio_formats = [f for f in formats if f['TBR'] and f['VCODEC'] == 'audio only']
    max_tbr_audios = {}
    for audio in audio_formats:
        lang = audio['MORE INFO'].split(' ')[0][1:3]
        if lang == 'fil':
            lang = 'tl'
        if lang in language_map:
            if lang not in max_tbr_audios or int(audio['TBR'][:-1]) > int(max_tbr_audios[lang]['TBR'][:-1]):
                max_tbr_audios[lang] = audio

    for idx, (lang, audio) in enumerate(max_tbr_audios.items(), 1):
        audio_file = f"archivos/audio-{lang}-{video_title}.{audio['EXT']}"
        print(f"Descargando audio {idx}/{len(max_tbr_audios)}: ID {audio['ID']} (Idioma: {lang}) en {audio_file}")
        subprocess.run(['yt-dlp', '-f', audio['ID'], '-o', audio_file, url])

    return list(max_tbr_audios.keys())


def download_and_convert_subtitles(url, video_title, audio_languages):
    try:
        result = subprocess.run(['yt-dlp', '--list-subs', url], capture_output=True, text=True)
        output = result.stdout

        lines = output.strip().split('\n')
        subtitle_formats = []

        for line in lines:
            if 'vtt' in line:
                sub_format = line.split()[0]
                if '-' not in sub_format and sub_format in language_map:
                    subtitle_formats.append(sub_format)

        print(f"Se encontraron {len(subtitle_formats)} subtítulos:")
        for idx, sub_format in enumerate(subtitle_formats, 1):
            print(f"{idx}. {sub_format}")

        for idx, sub_format in enumerate(subtitle_formats, 1):
            subtitle_file = f"archivos/subtitle-{sub_format}-{video_title}.vtt"
            print(f"Descargando subtítulo {idx}/{len(subtitle_formats)}: {sub_format} en {subtitle_file}")
            subprocess.run(
                ['yt-dlp', '--sub-lang', sub_format, '--sub-format', 'vtt', '--write-sub', '--skip-download', '-o',
                 subtitle_file, url])

            # Ajustar el nombre del archivo descargado si tiene un sufijo adicional
            possible_downloaded_file = f"{subtitle_file}.{sub_format}.vtt"
            if os.path.exists(possible_downloaded_file):
                print(f"Archivo encontrado: {possible_downloaded_file}, renombrando a {subtitle_file}")
                os.rename(possible_downloaded_file, subtitle_file)
            else:
                print(f"Archivo {possible_downloaded_file} no encontrado, verificando {subtitle_file}")

        vtt_files = [f for f in os.listdir('archivos') if f.endswith('.vtt')]
        for idx, vtt_file in enumerate(vtt_files, 1):
            srt_file = vtt_file.replace('.vtt', '.srt')
            vtt_path = os.path.join('archivos', vtt_file)
            srt_path = os.path.join('archivos', srt_file)
            print(f"Convirtiendo subtítulo {idx}/{len(vtt_files)}: {vtt_path} a {srt_path}")
            with open(vtt_path, 'r', encoding='utf-8') as f:
                content = f.read().split('\n\n')[1:]
                with open(srt_path, 'w', encoding='utf-8') as srt:
                    for i, segment in enumerate(content, 1):
                        srt.write(str(i) + '\n' + segment.replace('WEBVTT\n', '').replace('.', ',') + '\n\n')

    except Exception as e:
        print(f"ERROR AL DESCARGAR O PROCESAR SUBTÍTULOS: {str(e).upper()}")

def merge_media(directory):
    # Filtrar archivos de vídeo, audio y subtítulos
    video_file = None
    audio_files = []
    subtitle_files = []

    for filename in os.listdir(directory):
        if filename.startswith("video-"):
            video_file = os.path.join(directory, filename)
        elif filename.startswith("audio-"):
            audio_files.append(os.path.join(directory, filename))
        elif filename.startswith("subtitle-"):
            subtitle_files.append(os.path.join(directory, filename))

    if not video_file:
        print("No se encontró ningún archivo de vídeo.")
        return

    # Filtrar archivos de audio y subtítulos según la whitelist y priorizar, eliminando duplicados
    audio_files = list(dict.fromkeys([f for f in audio_files if f.split('-')[1] in language_map]))
    subtitle_files = list(dict.fromkeys([f for f in subtitle_files if f.split('-')[1] in language_map]))

    # Eliminar el archivo de salida si ya existe
    output_file = os.path.join(directory, "final_video.mkv")
    if os.path.exists(output_file):
        os.remove(output_file)

    # Construir el comando de ffmpeg
    ffmpeg_cmd = ["ffmpeg", "-i", video_file]

    audio_files = list(set(audio_files))

    # Ordenar los archivos según la prioridad de los idiomas
    audio_files.sort(key=lambda x: (
        priority_languages.index(x.split('-')[1]) if x.split('-')[1] in priority_languages else len(priority_languages),
        x))

    # Añadir pistas de audio al comando
    for audio_file in audio_files:
        ffmpeg_cmd.extend(["-i", audio_file])

    subtitle_files = list(set([file for file in subtitle_files if file.endswith('.srt')]))
    subtitle_files.sort(key=lambda x: (
        priority_languages.index(x.split('-')[1]) if x.split('-')[1] in priority_languages else len(priority_languages),
        x))

    # Añadir pistas de subtítulos al comando
    for subtitle_file in subtitle_files:
        ffmpeg_cmd.extend(["-i", subtitle_file])

    # Mapear pistas de audio y subtítulos correctamente
    ffmpeg_cmd.extend(["-map", "0:v"])  # Asegurar que el vídeo se incluya

    audio_index = 1
    subtitle_index = len(audio_files) + 1
    for i, audio_file in enumerate(audio_files):
        language_code = audio_file.split('-')[1]
        language_name = language_map.get(language_code, language_code)
        ffmpeg_cmd.extend([
            "-map", f"{i + 1}:a",
            f"-metadata:s:a:{i}", f"language={language_code}",
            f"-metadata:s:a:{i}", f"title={language_name}"
        ])

    for i, subtitle_file in enumerate(subtitle_files): 
        language_code = subtitle_file.split('-')[1]
        language_name = language_map.get(language_code, language_code)
        ffmpeg_cmd.extend([
            "-map", f"{i + subtitle_index}:s",
            f"-metadata:s:s:{i}", f"language={language_code}",
            f"-metadata:s:s:{i}", f"title={language_name}"
        ])

    ffmpeg_cmd.extend(["-c:v", "copy", "-c:a", "aac", "-c:s", "srt", output_file])

    # Ejecutar el comando de ffmpeg con progreso en tiempo real
    process = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True,
                               encoding='utf-8')
    for line in process.stdout:
        print(line, end='')

# Rellenar url
url = ""
video_title = get_video_title(url)
formats = get_yt_dlp_formats(url)
audio_languages = download_video_and_audio(url, formats, video_title)
download_and_convert_subtitles(url, video_title, audio_languages)
merge_media("archivos")
