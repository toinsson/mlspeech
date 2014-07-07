#!/usr/local/bin/python


from os import path
import logging
import io, subprocess, wave
import json
import urllib2 as urllib
from urllib2 import Request, urlopen
from simplejson import loads
from simplejson.scanner import JSONDecodeError

from wave import Error

class Decoder(object):
    """
    Wrapper for Google speech recognition web API.
    """
    def __init__(self, **kwargs):
        super(Decoder, self).__init__()
        self.logger = logging.getLogger('debug')
        self.recognizer = Recognizer()

    def decode(self, f, filename, keyword, decoderMatch):

        # try:
        with WavFile(f) as source:
            audio = self.recognizer.record(source)
            try:
                hypstr = self.recognizer.recognize(audio)
            except LookupError:
                self.logger.debug('no match: %s - %s', f, filename)
                hypstr = ''
        # except Error:
        #     self.logger.debug('wave file error %s %s', f, filename)
        #     hypstr = ''

        if hypstr != '':
            keywords = list()
            for k,v in keyword.iteritems():
                if v.name in hypstr:  # this is the same as k actually
                    keywords.append(v.name)

            fileId = path.splitext(filename)[0]
            decoderMatch[fileId] = keywords
            self.logger.debug('%s - %s', fileId, keywords)

class AudioSource(object):
    pass

class AudioData(object):
    def __init__(self, rate, data):
        self.rate = rate
        self.data = data

class WavFile(AudioSource):
    def __init__(self, filename_or_fileobject):
        if isinstance(filename_or_fileobject, str):
            self.filename = filename_or_fileobject
        else:
            self.filename = None
            self.wav_file = filename_or_fileobject
        self.stream = None

    def __enter__(self):
        if self.filename: self.wav_file = open(self.filename, "rb")
        self.wav_reader = wave.open(self.wav_file, "rb")
        self.SAMPLE_WIDTH = self.wav_reader.getsampwidth()
        self.RATE = self.wav_reader.getframerate()
        self.CHANNELS = self.wav_reader.getnchannels()
        assert self.CHANNELS == 1 # audio must be mono
        self.CHUNK = 4096
        self.stream = WavFile.WavStream(self.wav_reader)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.filename: self.wav_file.close()
        self.stream = None

    class WavStream(object):
        def __init__(self, wav_reader):
            self.wav_reader = wav_reader

        def read(self, size = -1):
            if size == -1:
                return self.wav_reader.readframes(self.wav_reader.getnframes())
            return self.wav_reader.readframes(size)

import socket

class Recognizer(AudioSource):
    def __init__(self, language = "en-US", key = "AIzaSyBOti4mM-6x9WDnZIjIeyEU21OpBXqWBgw"):
        self.key = key
        self.language = language
        self.logger = logging.getLogger('debug')

        self.energy_threshold = 100 # minimum audio energy to consider for recording
        self.pause_threshold = 0.8 # seconds of quiet time before a phrase is considered complete
        self.quiet_duration = 0.5 # amount of quiet time to keep on both sides of the recording

    def record(self, source, duration = None):
        assert isinstance(source, AudioSource) and source.stream

        frames = io.BytesIO()
        seconds_per_buffer = source.CHUNK / source.RATE
        elapsed_time = 0
        while True: # loop for the total number of chunks needed
            elapsed_time += seconds_per_buffer
            if duration and elapsed_time > duration: break

            buffer = source.stream.read(source.CHUNK)
            if len(buffer) == 0: break
            frames.write(buffer)

        frame_data = frames.getvalue()
        frames.close()
        return AudioData(source.RATE, frame_data)

    def recognize(self, audio_data, show_all = False):
        assert isinstance(audio_data, AudioData)

        url = "http://www.google.com/speech-api/v2/recognize?client=chromium&lang=%s&key=%s" % (self.language, self.key)
        self.request = urllib.Request(url, data = audio_data.data, headers = {"Content-Type": "audio/l16; rate=%s" % audio_data.rate})

        # check for invalid key response from the server
        try:
            response = urllib.urlopen(self.request, timeout=119)
        except urllib.URLError as e:
            self.logger.debug('urllib.URLError - %s', e)
            return []
        except socket.timeout as e:
            self.logger.debug('socket.timeout - %s', e)
            return []
        except Exception as e:
            self.logger.debug('urllib2.ulropen fail - %s', e)
            return []

        try:
            response_text = response.read().decode("utf-8")
        except Exception as e:
            self.logger.debug('response.read fail - %s', e)
            return []

        # ignore any blank blocks
        actual_result = []
        for line in response_text.split("\n"):
            if not line: continue
            result = json.loads(line)["result"]
            if len(result) != 0:
                actual_result = result[0]

        # make sure we have a list of transcriptions
        if "alternative" not in actual_result:
            raise LookupError("Speech is unintelligible")

        # return the best guess unless told to do otherwise
        if not show_all:
            for prediction in actual_result["alternative"]:
                if "confidence" in prediction:
                    return prediction["transcript"]
            raise LookupError("Speech is unintelligible")

        spoken_text = []

        # check to see if Google thinks it's 100% correct
        default_confidence = 0
        if len(actual_result["alternative"])==1: default_confidence = 1

        # return all the possibilities
        for prediction in actual_result["alternative"]:
            if "confidence" in prediction:
                spoken_text.append({"text":prediction["transcript"],"confidence":prediction["confidence"]})
            else:
                spoken_text.append({"text":prediction["transcript"],"confidence":default_confidence})
        return spoken_text
