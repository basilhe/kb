# -*- coding: utf-8 -*-
"""
Created on Tue Jun 14 15:35:40 2022
@author: hans
"""

from moviepy.editor import TextClip, VideoFileClip, vfx, CompositeVideoClip, ImageClip, AudioFileClip
from os import listdir, makedirs, cpu_count
from os.path import isfile, join, isdir, basename, normpath
import itertools
from random import randint

import argparse

import glob
from csv import reader
import re
import pathlib

BP = 'BP'

def emptyDir(path):
    import os, shutil
    for filename in os.listdir(path):
        file_path = os.path.join(path, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))

def buildTextClip(title, duration=5, width=720, position=400):
    txt_clip = TextClip(title, color='white', font='Rubik-Medium', fontsize=200, stroke_color='orange', stroke_width=3.0, align='center', size=(width - 20,0))
    return txt_clip.set_duration(duration).set_position((10,position))

def mergeVideoClips(video_clips, audioClip, audioinfo, imageClip, keep_sequence):
    total_duration = 0
    for i in range(len(video_clips)):
        video = video_clips[i]
        if not keep_sequence:
            duration = audioinfo[i] if i == 0 else audioinfo[i] - audioinfo[i-1]
            video = video.fx(vfx.speedx, video.duration * 1000 / duration)
        if (i > 0):
            video = video.set_start(total_duration if keep_sequence else (audioinfo[i-1] / 1000))
        video_clips[i] = video
        total_duration += video.duration
    x = int((video_clips[0].w - imageClip.size[0])/2)
    y = int(video_clips[0].h / 3 - imageClip.size[1] - 100)

    video_clips.append(imageClip.set_position((x, y)).set_duration(total_duration if keep_sequence else (audioinfo[-1] / 1000)))
    outVideoClip = CompositeVideoClip(video_clips)
    if keep_sequence:
        outVideoClip = outVideoClip.fx(vfx.speedx, total_duration / (audioinfo[-1] / 1000))
    return ''.join([v.filename for v in video_clips[0:-1]]), outVideoClip.set_audio(audioClip) if audioClip is not None else outVideoClip.without_audio()

# ????????????????????????????????????
def gen_sequence(items, groups):
    groupitems = {}
    for x in groups:
        groupitems[x] = [item for item in items if item.startswith(x)]
        
    result = []
    
    head = groupitems[groups[0]]
    tail = groupitems[groups[-1]]
    for x in range(len(head)):
        h = head[x]
        for y in range(len(tail)):
            t = tail[y]
            item = [h]
            for i in range(1, len(groups) -1):
                curr = groupitems[groups[i]]
                item.append(curr[randint(0, len(curr) - 1)])
            item.append(t)
            result.append(item)
    return result
    
def gen_matrix(items, column, bpcount):
    matrix = set(itertools.permutations(items, column))

    columns = {}
    
    result = []
    while len(matrix) > 0:
        item = matrix.pop()
        if BP not in item:
            continue
        
        found = False
        for x in range(len(item)):
            if item[x] == BP:
                bpfound = 0
                for p in range(bpcount):
                    if '%s%d_%d' % (item[x], x, p) in columns:
                        bpfound += 1
                if bpfound == bpcount:
                    found = True
                    break
            elif '%s%d' % (item[x], x) in columns:
                found = True
                break
        if not found:
            item = list(item)
            for x in range(len(item)):
                if item[x] == BP:
                    for p in range(bpcount):
                        if not '%s%d_%d' % (item[x], x, p) in columns:
                            columns['%s%d_%d' % (item[x], x, p)] = True
                            item[x] = '%s%d' % (BP,p)
                            break
                else:
                    columns['%s%d' % (item[x], x)] = True
            result.append(item)
    
    return result
        
def main():     
    parser = argparse.ArgumentParser(description="????????????")
    parser.add_argument("audio_dir", help="????????????")
    parser.add_argument('--remove_audio', action='store_true', help='????????????')
    parser.add_argument('--keep_sequence', action='store_true', help='????????????')
    parser.add_argument("audio_info", help="??????????????????")
    parser.add_argument("sku_code", help="SKU??????")
    parser.set_defaults(remove_audio=False, keep_sequence=False)
    args = parser.parse_args()
    
    if not isdir(args.sku_code) or not isdir(args.audio_dir):
        print("????????????????????????????????????????????????")
        return
    
    if not isfile(args.audio_info):
        print("???????????????????????????")
        return
    
    skucode = basename(normpath(args.sku_code))
    moviepath = skucode
    adwordspath = join(moviepath, '?????????')

    output_dir = "out_%s" % skucode
    
    parts = skucode.split('_')
    skucode = parts[0]
    skugroup = parts[1] if len(parts) > 1 else '0'
    
    if not isdir(output_dir):
        makedirs(output_dir)
    else:
        emptyDir(output_dir)        

    if not isdir(adwordspath):
        print("????????????????????????")
        return

    groups = []    
    if args.keep_sequence:
        moviefiles = [f for f in listdir(moviepath) if isfile(join(moviepath, f)) and re.match(r'%s[A-Z]O[0-9]+.*\.' % skucode, f)]
        groups = sorted(set([re.findall(r'%s[A-Z]O' % skucode, f)[0] for f in moviefiles]))
    else:
        moviefiles = [f for f in listdir(moviepath) if isfile(join(moviepath, f)) and re.match(r'%sS[0-9]+.*\.' % skucode, f)]
    descfiles = [f for f in listdir(moviepath) if isfile(join(moviepath, f)) and re.match(r'.*\.(mp3|m4a|wav)', f)]
    
    audiopath = args.audio_dir
    audiofiles = glob.glob(join(audiopath, '*.m*'))
    
    if len(moviefiles) == 0 or len(audiofiles) == 0:
        print("?????????????????????????????????")
        return

    videosuffix = pathlib.Path(moviefiles[0]).suffix
    bpmoviefiles = [f for f in listdir(moviepath) if isfile(join(moviepath, f)) and re.match(r'%sB[0-9]+.*\.' % skucode, f)]

    if len(bpmoviefiles) == 0 and not args.keep_sequence:
        print("?????????????????????")
        return
    
    print('?????????????????????...')
    adwordClips = [ImageClip(join(adwordspath, f)) for f in listdir(adwordspath)]
    adwordcount= len(adwordClips)
    print('?????? %d ?????????????????????' % adwordcount)    
    
    print('????????????????????????...')
    audiomin = 100
    audiomax = 0
    audioinfo = {}
    with open(args.audio_info, 'r') as data:
        csv_reader = reader(data)
            #print(header)
        for row in csv_reader:
            # row variable is a list that represents a row in csv
            name = row[0]
            s = re.findall(r'([0-9]*)(.*)(\..*)?',name)
            sequence = s[0][0]
            name = s[0][1]
            suffix = s[0][2]
            points = list(map(int, row[1:]))
            audioinfo[sequence] = (name, suffix, points)
            if len(points) < audiomin:
                audiomin = len(points)
            if len(points) > audiomax:
                audiomax = len(points)
    print('??????????????????????????????')
    videoidx = 0
    
    bpClips = []
    descClips = []
    if args.keep_sequence:
        print('??????????????????...', descfiles)
        descClips = [AudioFileClip(join(moviepath, f)) for f in descfiles]
            
        print('????????????????????????')
    else:
        print('??????????????????...')
        bpClips = [VideoFileClip(join(moviepath, f)) for f in bpmoviefiles]
            
        print('????????????????????????')
    videoClips = {}
    def getVideoClips(filename):
        if filename in videoClips:
            print('????????????????????? %s' % filename)
            return videoClips[filename]
        videoClip = VideoFileClip(join(moviepath, filename))
        videoClips[filename] = videoClip
        print('???????????? %s' % filename)
        return videoClip
    
    audio = None
    for sequence, (name, suffix, audioinfo) in audioinfo.items():
        print('???????????? %s ...' % name)
        if not args.remove_audio and not args.keep_sequence:
            audiofilename = ''.join([sequence, name, suffix])
            audio = AudioFileClip(join(audiopath, audiofilename)).subclip(t_end=audioinfo[-1]/1000)
        video_count = len(audioinfo)
        print('???????????? %s ?????????%d ?????????' % (name, video_count))
        print('??????????????????... %dx%d' % ((len(moviefiles) + 1, video_count) if not args.keep_sequence else (len(moviefiles), len(groups))))
        videomatrix = gen_matrix([*moviefiles, BP], video_count, len(bpClips)) if not args.keep_sequence else gen_sequence(moviefiles, groups)
        print('????????????????????????')
        while len(videomatrix) > 0:
            item = videomatrix.pop()
            print('??????????????????...')
            rndClips = [getVideoClips(f) if not f.startswith(BP) else bpClips[int(f.replace(BP, ''))] for f in item]
            print('????????????????????????')
            adwordIdx = randint(0, adwordcount - 1)
            imageClip = adwordClips[adwordIdx]
            print('????????????...')
            if len(descfiles) > 0 and args.keep_sequence:
                descIdx = randint(0, len(descfiles) - 1)
                audio = descClips[descIdx]
                
            filenamelink, gen_video = mergeVideoClips(rndClips, audio, audioinfo, imageClip, args.keep_sequence)
            filenamelink = filenamelink.replace(join(moviepath, skucode), '').replace(videosuffix, '_')[0:-1]
            print('??????????????????: %s' % filenamelink)
        
            filename = '%s_%s_%02i_%s_%s.mp4' % (skucode, skugroup, videoidx, sequence, filenamelink)
            print('????????????: %s...' % filename)
            gen_video.write_videofile(join(output_dir, filename), audio_codec='aac', threads=cpu_count(), verbose=False)
            print('????????????: %s??????' % filename)
            videoidx += 1
        
    print('??????????????????????????????????????? %d ?????????' % videoidx)

if __name__ == "__main__":
    main()
