from importlib.resources import files
from importlib.resources import as_file
import sys

if sys.platform == "win32":
    import winsound
else:
    import simpleaudio as sa


def get_audio_path(filename):
    audio_dir = files("up_watcher").joinpath("assets")
    return audio_dir.joinpath(filename)


def play_audio(filename):
    audio_path = get_audio_path(filename)
    with as_file(audio_path) as audio_file:
        if sys.platform == "win32":
            winsound.PlaySound(str(audio_file), winsound.SND_FILENAME)
            return

        wave_obj = sa.WaveObject.from_wave_file(str(audio_file))
        play_obj = wave_obj.play()
        play_obj.wait_done()
