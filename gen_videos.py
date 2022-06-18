# -*- coding: utf-8 -*-
"""
Created on Tue Jun 14 15:35:40 2022

@author: hans
"""

from moviepy.editor import TextClip, VideoFileClip, vfx, CompositeVideoClip, ImageClip
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

def buildTextClip(title, duration=5, width=720):
    txt_clip = TextClip(title, color='white', font='Rubik-Medium', fontsize=200, stroke_color='orange', stroke_width=3.0, align='center', size=(width - 20,0))
    return txt_clip.set_duration(duration).set_position((10,500))

def mergeVideoClips(video_clips, audioClip, audioinfo, imageClip):
    
    for i in range(len(video_clips)):
        video = video_clips[i]
        duration = audioinfo[i] if i == 0 else audioinfo[i] - audioinfo[i-1]
        video = video.fx(vfx.speedx, video.duration * 1000 / duration)
        if (i > 0):
            video = video.set_start(audioinfo[i-1] / 1000)
        video_clips[i] = video
    x = int((video_clips[0].w - imageClip.size[0])/2)
    y = int(video_clips[0].h / 3 - imageClip.size[1])
    video_clips.append(imageClip.set_position((x, y)).set_duration(audioinfo[-1] / 1000))
    outVideoClip = CompositeVideoClip(video_clips)
    return ''.join([v.filename for v in video_clips[0:-1]]), outVideoClip.set_audio(audioClip) if audioClip is not None else outVideoClip.without_audio()

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
    parser.add_argument("audio_dir", help="音乐目录")
    parser.add_argument('--remove_audio', action='store_true', help='清除音频')
    parser.add_argument("audio_info", help="音乐卡点文件")
    parser.add_argument("sku_code", help="SKU目录")
    parser.set_defaults(remove_audio=False)
    args = parser.parse_args()
    
    if not isdir(args.sku_code) or not isdir(args.audio_dir):
        print("视频目录或音乐目录请指定有效目录")
        return
    
    if not isfile(args.audio_info):
        print("音乐卡点文件不存在")
        return
    
    skucode = basename(normpath(args.sku_code))
    moviepath = skucode
    adwordspath = join(moviepath, '广告语')

    output_dir = "out_%s" % skucode
    
    if not isdir(output_dir):
        makedirs(output_dir)
    else:
        emptyDir(output_dir)        

    if not isdir(adwordspath):
        print("广告语目录不存在")
        return
    
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
    
    print('加载广告语图片...')
    adwordClips = [ImageClip(join(adwordspath, f)) for f in listdir(adwordspath)]
    adwordcount= len(adwordClips)
    print('加载 %d 个广告语图片！' % adwordcount)    
    
    print('加载音乐卡点信息...')
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
    print('加载音乐卡点信息成功')
    videoidx = 0
    print('加载爆点视频...')
    bpClips = [VideoFileClip(join(moviepath, f)) for f in bpmoviefiles]
        
    print('加载爆点视频成功')
    videoClips = {}
    def getVideoClips(filename):
        if filename in videoClips:
            print('使用已缓存视频 %s' % filename)
            return videoClips[filename]
        videoClip = VideoFileClip(join(moviepath, filename))
        videoClips[filename] = videoClip
        print('缓存视频 %s' % filename)
        return videoClip
    
    audio = None
    for name, audioinfo in audioinfo.items():
        print('加载音频 %s ...' % name)
        if not args.remove_audio:
            audio = VideoFileClip(join(audiopath, '%s.mp4' % name)).audio
        video_count = len(audioinfo)
        print('加载音频 %s 成功，%d 个卡点' % (name, video_count))
        print('生成视频矩阵... %dx%d' % (len(moviefiles) + 1, video_count))
        videomatrix = gen_matrix([*moviefiles, BP], video_count, len(bpClips))
        print('生成视频矩阵成功')
        while len(videomatrix) > 0:
            item = videomatrix.pop()
            print('加载矩阵视频...')
            rndClips = [getVideoClips(f) if not f.startswith(BP) else bpClips[int(f.replace(BP, ''))] for f in item]
            print('加载矩阵视频成功')
            adwordIdx = randint(0, adwordcount - 1)
            imageClip = adwordClips[adwordIdx]
            print('合成视频...')
            filenamelink, gen_video = mergeVideoClips(rndClips, audio, audioinfo, imageClip)
            filenamelink = filenamelink.replace(join(skucode, skucode), '').replace(videosuffix, '_')[0:-1]
            print('合成视频成功: %s' % filenamelink)
        
            filename = '%s%02i_%s.mp4' % (skucode, videoidx, filenamelink)
            print('输出视频: %s...' % filename)
            gen_video.write_videofile(join(output_dir, filename), audio_codec='aac', threads=cpu_count(), verbose=False)
            print('输出视频: %s成功' % filename)
            videoidx += 1
    print('所有视频合成完毕，一共合成 %d 个视频' % videoidx)

if __name__ == "__main__":
    main()
