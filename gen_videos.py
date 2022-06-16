# -*- coding: utf-8 -*-
"""
Created on Tue Jun 14 15:35:40 2022

@author: hans
"""

from moviepy.editor import TextClip, VideoFileClip, vfx, CompositeVideoClip
from os import listdir, makedirs
from os.path import isfile, join, isdir
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

def buildTextClip(title, duration=5, width=720):
    txt_clip = TextClip(title, color='white', font='Rubik-Medium', fontsize=200, stroke_color='orange', stroke_width=3.0, align='center', size=(width - 20,0))
    return txt_clip.set_duration(duration).set_pos((10,500))

def mergeVideoClips(video_clips, audioClip, audioinfo, title):
    
    for i in range(len(video_clips)):
        video = video_clips[i]
        duration = audioinfo[i] if i == 0 else audioinfo[i] - audioinfo[i-1]
        video = video.fx(vfx.speedx, video.duration * 1000 / duration)
        if (i > 0):
            video = video.set_start(audioinfo[i-1] / 1000)
        video_clips[i] = video

    text_clip = buildTextClip(title, width=video_clips[0].w, duration=audioinfo[-1] / 1000)
    video_clips.append(text_clip)
    outVideoClip = CompositeVideoClip(video_clips)
    return ''.join([v.filename for v in video_clips[0:-1]]), outVideoClip.set_audio(audioClip)

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
    parser = argparse.ArgumentParser(description="视频混剪")
    parser.add_argument("sku_code", help="SKU编号")
    parser.add_argument("audio_dir", help="音乐目录")
    parser.add_argument("audio_info", help="音乐卡点文件")
    parser.add_argument("title_file", help="标题文件")
    parser.add_argument("output_dir", help="视频输出目录")
    args = parser.parse_args()
    
    if not isdir(args.sku_code) or not isdir(args.audio_dir):
        print("视频目录或音乐目录请指定有效目录")
        return
    
    if not isfile(args.audio_info):
        print("音乐卡点文件不存在")
        return
    
    if not isfile(args.title_file):
        print("标题文件不存在")
        return
    
    if not isdir(args.output_dir):
        makedirs(args.output_dir)
    else:
        emptyDir(args.output_dir)
        
    moviepath = args.sku_code
    skucode = args.sku_code
    
    moviefiles = [f for f in listdir(moviepath) if isfile(join(moviepath, f)) and re.match(r'%sS[0-9]+.*\.' % skucode, f)]
    
    audiopath = args.audio_dir
    audiofiles = glob.glob(join(audiopath, '*.mp4'))
    
    if len(moviefiles) == 0 or len(audiofiles) == 0:
        print("视频目录或音乐目录为空")
        return

    videosuffix = pathlib.Path(moviefiles[0]).suffix
    bpmoviefiles = [f for f in listdir(moviepath) if isfile(join(moviepath, f)) and re.match(r'%sB[0-9]+.*\.' % skucode, f)]

    if len(bpmoviefiles) == 0:
        print("未指定爆点视频")
        return
    
    with open(args.title_file, 'r') as f:
        titles = f.readlines()
        if len(titles) == 0:
            print("标题为空")
            return

    audiomin = 100
    audiomax = 0
    audioinfo = {}
    with open(args.audio_info, 'r') as data:
        csv_reader = reader(data)
            #print(header)
        for row in csv_reader:
            # row variable is a list that represents a row in csv
            name = row[0]
            points = list(map(int, row[1:]))
            audioinfo[name] = points
            if len(points) < audiomin:
                audiomin = len(points)
            if len(points) > audiomax:
                audiomax = len(points)
    
    videoidx = 0
    bpClips = [VideoFileClip(join(moviepath, f)) for f in bpmoviefiles]
    for name, audioinfo in audioinfo.items():
        audioClip = VideoFileClip(join(audiopath, '%s.mp4' % name))

        video_count = len(audioinfo)
        videomatrix = gen_matrix([*moviefiles, BP], video_count, len(bpClips))

        while len(videomatrix) > 0:
            item = videomatrix.pop()
            rndClips = [VideoFileClip(join(moviepath, f)) if not f.startswith(BP) else bpClips[int(f.replace(BP, ''))] for f in item]
        
            titleIdx = randint(0, len(titles) - 1)
            title = titles[titleIdx].replace("\\n", "\n")
        
            filenamelink, gen_video = mergeVideoClips(rndClips, audioClip.audio, audioinfo, title)
            filenamelink = filenamelink.replace(join(skucode, skucode), '').replace(videosuffix, '_')[0:-1]
        
            filename = '%s%02i_%s.mp4' % (skucode, videoidx, filenamelink)
            gen_video.write_videofile(join(args.output_dir, filename))
            videoidx += 1

if __name__ == "__main__":
    main()
