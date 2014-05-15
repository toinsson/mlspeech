#!/usr/local/bin/python

## to be stored in a constant definition file
devRoot = "/Users/toine/Documents/dev"

## imports std
import itertools
import os
import sys
import imp
import logging
import time

## imports local
import matplotlib as plt
import h5py
import numpy as np
import wave
sys.path.append(devRoot+"/bob.spear-1.1.2")

from collections import namedtuple


def secondsToStr(t):
    return "%d:%02d:%02d.%03d" % \
        reduce(lambda ll,b : divmod(ll[0],b) + ll[1:],
            [(t*1000,),1000,60,60])

class VadSeg(object):
    """
    Performs the segmentation of file.wav through voice activity detection and
    stores the segments in file.as.

    file.as format is:
    filename
    id_0
    startChunk:stopChunk
    id_1
    startChunk:stopChunk
    ...

    TODO:
    - optimize the constants, might depend on distribution of silence between utterances
    - try out different Voice Activity Detection algorithm, especially in case of a noisy env.
    """
    def __init__(self, dirname, filename, vad="default"):
        """
        wavFile is the filename of the file.wav to be segmented.
        vad is the algorithm for the VAD, default is energy, modulation is available too.
        """
        super(VadSeg, self).__init__()

        self.dirname = dirname
        self.filename = filename

        self.wavFile = wave.open(os.path.join(dirname, filename+".wav"), 'rb')
        #self.wavFile = wavFile
        self.hdf5FileName = os.path.join(dirname, filename+".hdf5")
        #self.hdf5File = self.wavFile.strip(".wav")+".hdf5"

        self.asFile = open(os.path.join(dirname, self.filename+".as"), "w")

        self.vadCfg = imp.load_source("cfg_vad", devRoot+"/bob.spear-1.1.2/config/preprocessing/energy.py")
        self.vad = self.vadCfg.preprocessor(self.vadCfg)

        ## segmentation constants
        ## the VAD output 1 sample per 10ms, hence the constants represents 100ms and 500ms
        self.SMALLEST_GAP_MS = 15 # 100 / 10
        self.SMALLEST_CHUNK_MS = 55 # 500 / 10

        ## logger 
        self.logger = logging.getLogger(__name__)

    def __del__(self):
        """Close the file objects opened at creation."""
        self.wavFile.close()

    def perform_vad(self):
        """Perform the voice activity detection on file.wav and store the result in file.hdf5."""
        startTime = time.time()
        self.logger.debug('%s', 'start VAD')

        fileIn = os.path.join(self.dirname, self.filename+".wav")
        fileOut = self.hdf5FileName  ## os.path.join(self.dirname, self.filename+".hdf5")
        self.vad(fileIn, fileOut)

        self.logger.debug('%s %f', 'finish VAD: ', time.time() - startTime)

    def perform_segmentation(self):
        """
        Perform the segmentation of file.wav based on file.hdf5.
        TODO: 
        - split this in private helper functions
        - use namedtuple for segments, not access of segment[X]
        - include a little bit of surroundings when saving file
        """

        Segment = namedtuple('Segment', ['start', 'end', 'length', 'separation'])

        hdf5File = h5py.File(self.hdf5FileName, 'r+')
        ar = hdf5File.values()
        npar = np.array(ar)

        ## find the non zero indices
        nparNonZero = npar.nonzero()[1]

        ## create a fictive island at the end
        nparNonZero = np.append(nparNonZero, nparNonZero[-1]+2)

        ##
        ## find the segments boundaries
        ##
        a, b = itertools.tee(nparNonZero)
        next(b, None)

        segments = []

        start = nparNonZero[0]
        for (left, right) in itertools.izip(*[a, b]):
            if left != right-1:
                end = left
                lenght = end - start
                separation = right - end
                segments.append(Segment(start, end, lenght, separation))
                start = right

        ##
        ## merge the "adjacent" segments and drop the small ones
        ##
        a, b = itertools.tee(segments)
        next(b, None)

        filtSeg = []
        mergeFlag = False
        for (left, right) in itertools.izip(*[a,b]):
            # if close, merge
            if left.separation < self.SMALLEST_GAP_MS:
                if mergeFlag:
                    # pop last and replace
                    last = filtSeg.pop() 
                    filtSeg.append(Segment(last.start, right.end, right.end - last.start, 0))
                else:
                    # take left
                    mergeFlag = True
                    filtSeg.append(Segment(left.start, right.end, right.end - left.start, 0))

            elif mergeFlag:
                # check if last merge produced a big chunk, otherwise pop it
                if filtSeg[-1].length < self.SMALLEST_CHUNK_MS:
                    filtSeg.pop()

                mergeFlag = False

            else:
                if left.length > self.SMALLEST_CHUNK_MS:
                    filtSeg.append(left)
                else:
                    pass

        ## save the chunks in file.as
        self.asFile.write(self.filename+'\n')
        for (num, chunk) in enumerate(filtSeg):
            self.asFile.write(str(num)+'\n')
            self.asFile.write(str(chunk[0])+'0-'+str(chunk[1])+'0\n')
        ## hdf5 file contains 1 sample per 160 wav sample, that is 1 sample represents 10ms at a
        ## sampling rate of 16kHz, so adding a zero makes it into ms.
        ## ex: 154 in hd5f represent 1540ms in wav

        ## recreate the hdf5 file
        a, b = itertools.tee(filtSeg)
        next(b, None)

        A = np.zeros(filtSeg[0][0], dtype=int)

        for (left, right) in itertools.izip(*[a, b]):
            A = np.append(A, np.ones(left[2]))
            A = np.append(A, np.zeros(right[0] - left[1]))

        hdf5File.create_dataset("filtered_vad", (len(A), ), dtype="i2")
        hdf5File["/filtered_vad"][...] = np.array(A)


## implement testing or printing
def print_for_test():
    f = h5py.File("lex-chocolate-1min.hdf5")
    ar = f.values()
    npar = np.array(ar)
    x1 = np.linspace(0, len(npar[0]), num=len(npar[0]))

    wavFile = wave.open("lex-chocolate-1min.wav")
    (nchannels, sampwidth, framerate, nframes, comptype, compname) = wavFile.getparams()
    frames = wavFile.readframes(-1)
    data = np.fromstring(frames, "Int16")
    x2 = np.linspace(0, len(data), num=len(data))

    f1 = plt.figure(1)
    plt.plot(x1*160, npar[0]*max(data), x2, data);
    f1.show()

    xA = np.linspace(0, len(A), num=len(A))
    f2 = plt.figure(2)
    plt.plot(xA*160/16000, A*max(data), x2/16000, data);
    f2.show()


class ChunkerFromAsFile(object):
    """
    Chunk wav from file.wav based on file.as.
    The as file is obtained from VadSeg class.

    file.as format is:
    filename
    id_0
    startChunk:stopChunk
    id_1
    startChunk:stopChunk
    ...

    where startChunk and stopChunk are start and stop time of the chunk to 
    create in milliseconds.

    TODO:
    - include a window that take a bit of audio outside the chunk to smooth 
    the VAD segmenting. Useful when splitting in the middle of a sentence, word. 
    """
    def __init__(self, dirname, filename):
        """
        Init the class with file.wav and file.as.
        """
        super(ChunkerFromAsFile, self).__init__()

        self.dirname = dirname
        self.filename = filename

        self.wavFile = wave.open(os.path.join(dirname, filename+".wav"), 'rb')
        self.asFile = open(os.path.join(dirname, self.filename+".as"), "r")

        self.wavDir = dirname+"/wav"

        self.window = 50  # take 20ms around the sound sample tpo smooth the VAD selection

    def __del__(self):
        """Close the file objects opened at creation."""
        self.wavFile.close()
        self.asFile.close()

    def create_chunks(self):
        """Create the utterance wav chunks out of wavFile from the mtFile."""
        # create wav directory    
        try:
            os.mkdir(self.wavDir)
        except OSError as e:
            ## log.error - file exist
            pass

        wavFile = self.wavFile
        (nchannels, sampwidth, framerate, nframes, comptype, compname) = wavFile.getparams()
        asFile = self.asFile
        asFile.readline() # dump the filename as the first line

        ## get 2 same iterators on f
        for (id , time) in itertools.izip(*([iter(asFile)]*2)):
            # write .fileids and .transcription files
            outFilename = self.filename + "_" + '{:04d}'.format(int(id.strip()))

            [msSt, msEd] = time.strip().split("-")
            frameSt = int((float(msSt) - self.window) * framerate / 1000)
            frameEd = int((float(msEd) + self.window) * framerate / 1000)

            if frameSt < 0:
                frameSt = 0
            if frameEd > nframes:
                frameEd = nframes

            wavFile.setpos(frameSt)
            chunk = wavFile.readframes(frameEd - frameSt)
            
            out = wave.open(self.wavDir+"/"+outFilename+".wav", "w")
            # writeframes will take care of overwritting nframes
            out.setparams((nchannels, sampwidth, framerate, nframes, comptype, compname))
            out.writeframes(chunk)
            out.close()

## get a transcript file and create the differents CMU Sphinx files needed
class ChunkerFromMtFile(object):
    """
    Chunk wav from file.wav based on file.mt.
    This will also create fileids and transcription files for CMU-Sphinx decoding.
    
    mt means "manual transcription". The mt format is:
    "filename"
    1
    "min:sec.ms-min:sec.ms"
    "utterance 1"
    2
    "min:sec.ms-min:sec.ms"
    "utterance 2"
    ...
    """

    def __init__(self, dirname, filename):
        """Provide the directory name that contains filename.wav and filename.mt."""
        super(ChunkerFromMtFile, self).__init__()
        
        self.dirname = dirname
        self.filename = filename

        # check for file.wav and file.mt
        self.wavFile = wave.open(os.path.join(dirname, filename+".wav"), 'rb')
        self.mtFile = open(os.path.join(dirname, filename+".mt"), 'r')
        self.wavDir = dirname+"/wav"
        self.transcriptionFile = open(os.path.join(dirname, self.filename+".transcription"), "w")
        self.fileidsFile = open(os.path.join(dirname, self.filename+".fileids"), "w")

    def __del__(self):
        """Close the file objects opened at creation."""
        self.wavFile.close()
        self.mtFile.close()
        self.transcriptionFile.close()
        self.fileidsFile.close()

    def create_chunks(self):
        """Create the utterance wav chunks out of wavFile from the mtFile."""
        # create wav directory    
        try:
            os.mkdir(self.wavDir)
        except OSError as e:
            ## log.error - file exist
            pass

        wavFile = self.wavFile
        (nchannels, sampwidth, framerate, nframes, comptype, compname) = wavFile.getparams()

        mtFile = self.mtFile
        _ = mtFile.readline()

        #TODO: should I change the mt file format?
        # check filename == self.filename

        transcriptionFile = self.transcriptionFile
        fileidsFile = self.fileidsFile

        ## get 3 same iterators on f
        for [id , time, text] in itertools.izip(*([iter(mtFile)]*3)):
            # write .fileids and .transcription files
            outFilename = self.filename + "_" + id.strip()
            fileidsFile.write(outFilename+"\n")
            text = "<s> " + text.strip().upper() + "</s>" + " (" + outFilename + ")"
            transcriptionFile.write(text+"\n")

            [st, ed] = time.strip().split("-")
            msSt = float(st.split(":")[0])*60000 + float(st.split(":")[1])*1000
            msEd = float(ed.split(":")[0])*60000 + float(ed.split(":")[1])*1000
            frameSt = int(msSt * framerate/1000)
            frameEd = int(msEd * framerate/1000)
            wavFile.setpos(frameSt)
            chunk = wavFile.readframes(frameEd - frameSt)
            out = wave.open(self.wavDir+"/"+outFilename+".wav", "w")
            # writeframes will take care of overwritting nframes
            out.setparams((nchannels, sampwidth, framerate, nframes, comptype, compname))
            out.writeframes(chunk)
            out.close()

