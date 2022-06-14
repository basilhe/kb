# -*- coding: utf-8 -*-
"""
Created on Tue Jun 14 15:35:40 2022

@author: hans
"""

from moviepy.editor import TextClip, VideoFileClip, afx, vfx, CompositeVideoClip
from os import listdir, makedirs
from os.path import isfile, join, isdir
import itertools
from random import randint

import argparse
import uuid

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
    txt_clip = TextClip(title, color='white', fontsize=200, stroke_color='orange', align='center', size=(width,0))
    return txt_clip.set_duration(duration).set_pos((0,100))

def combineVideoClips(video_clips, audio_clip, title):
    padding = 1.5
    video_fx_list = [video_clips[0]]
    # set padding to initial video

    idx = video_clips[0].duration - padding
    total_duration = video_clips[0].duration
    for video in video_clips[1:]:
        video_fx_list.append(video.set_start(idx).crossfadein(padding))
        idx += video.duration - padding
        total_duration += video.duration

    text_clip = buildTextClip(title, width=video_clips[0].w, duration=int(total_duration/12 * 5))
    video_fx_list.append(text_clip)
                         
    outVideoClip = CompositeVideoClip(video_fx_list)
    if total_duration > 12:
        outVideoClip = outVideoClip.fx(vfx.speedx, total_duration / 12)
    audio = afx.audio_loop(afx.audio_fadeout(afx.audio_fadein(audio_clip, 1.0), 1.0),duration=outVideoClip.duration-1)
    return outVideoClip.set_audio(audio)

def main():            
    parser = argparse.ArgumentParser(description="视频混剪")
    parser.add_argument("video_dir", help="视频目录")
    parser.add_argument("audio_dir", help="音乐目录")
    parser.add_argument("title_file", help="标题文件")
    parser.add_argument("output_dir", help="视频输出目录")
    args = parser.parse_args()
    
    if not isdir(args.video_dir) or not isdir(args.audio_dir):
        print("视频目录或音乐目录请指定有效目录")
        return
    
    if not isfile(args.title_file):
        print("标题文件不存在")
        return
    
    if not isdir(args.output_dir):
        makedirs(args.output_dir)
    else:
        emptyDir(args.output_dir)
        
    moviepath = args.video_dir
    moviefiles = [f for f in listdir(moviepath) if isfile(join(moviepath, f))]
    
    audiopath = args.audio_dir
    audiofiles = [f for f in listdir(audiopath) if isfile(join(audiopath, f))]
    
    if len(moviefiles) == 0 or len(audiofiles) == 0:
        print("视频目录或音乐目录为空")
        return

    with open(args.title_file) as f:
        titles = f.readlines()
        if len(titles) == 0:
            print("标题为空")
            return
    
    
    for p in itertools.permutations(moviefiles, 2):
        videoClip0 = VideoFileClip(join(moviepath, p[0]))
        videoClip1 = VideoFileClip(join(moviepath, p[1]))
        
        audioIdx = randint(0, len(audiofiles) - 1)
        audioClip = VideoFileClip(join(audiopath, audiofiles[audioIdx]))
        
        titleIdx = randint(0, len(titles) - 1)
        title = titles[titleIdx].replace("\\n", "\n")
        
        gen_video = combineVideoClips([videoClip0, videoClip1], audioClip.audio, title)
        
        
        filename = str(uuid.uuid4())
        print("正在使用视频 %s 和 %s，音乐 %s 和标题 %s 生成" % (p[0], p[1], audiofiles[audioIdx], title))
        gen_video.write_videofile(join(args.output_dir, '%s.mp4' % filename))


if __name__ == "__main__":
    main()